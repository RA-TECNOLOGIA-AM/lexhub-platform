import { DataError } from '../errors.ts'
import type { AccessOverview, Member, MemberAccessUpdate, UnitRoleKey } from '../../types/index.ts'
import { catalog } from './catalog.ts'
import { groupOfArea, HUB_GROUPS } from './hubGroups.ts'
import type { createMembersStore } from './members.ts'

// Regras card a card das equipes do mock (team_id -> dashboards que liberam), como app.access_rules.
const RULES: Record<string, string[]> = {
    't-protocolo': ['protocolo-lexpre', 'pendencias-lexpre', 'peticionamento-lexpre', 'pre-protocolo'],
    't-comercial': ['comercial-lexpre', 'comissao-lexpre', 'nps'],
    't-pendencias': ['pendencias', 'pendencias-lexpre'],
}

// Grupos dos setores (app.team_group_grants) e quem vê tudo (app.teams.sees_all), como na carga do banco:
// Diretoria vê tudo da unidade.
const INITIAL_GROUPS: Record<string, string[]> = {}
const INITIAL_SEES_ALL = ['t-diretoria']

// O que cada cargo faz (app.role_permissions): Gestor e Controller veem tudo da unidade; Leitor não exporta.
const ROLES: AccessOverview['roles'] = [
    { key: 'gestor', sees_all: true, exports: true },
    { key: 'controller', sees_all: true, exports: true },
    { key: 'colaborador', sees_all: false, exports: true },
    { key: 'leitor', sees_all: false, exports: false },
]
const UNIT_ROLES = ROLES.map((r) => r.key)

const keysOf = (unit: string) => catalog.available.filter((d) => d.units.includes(unit)).map((d) => d.key)
const groupOf = Object.fromEntries(catalog.available.map((d) => [d.key, groupOfArea(d.area)]))
const isGroup = (slug: string) => HUB_GROUPS.some((g) => g.slug === slug)

// Módulo: o Acesso do mock, com as mesmas regras e mensagens de api.access_overview,
// api.update_member_access e api.set_team_groups. O mock é Owner/Desenvolvedor: gere todas as unidades.
// Parâmetro: a loja de Membros (editar acesso muda a lista de Membros também).
export function createAccessStore(members: ReturnType<typeof createMembersStore>) {
    const teamGroups: Record<string, string[]> = structuredClone(INITIAL_GROUPS)
    const seesAll = new Set(INITIAL_SEES_ALL)

    return {
        overview(unit: string | null): AccessOverview {
            const data = members.list()
            const units = [...data.units].sort((a, b) => a.code.localeCompare(b.code))
            const current = unit ?? units[0]?.code
            if (!units.some((u) => u.code === current)) throw new DataError(403, 'Você não gere acesso nesta unidade.')
            const teams = data.teams.map((t) => ({ ...t, sees_all: seesAll.has(t.id), groups: teamGroups[t.id] ?? [] }))
            const teamsOf = (key: string) =>
                teams
                    .filter(
                        (t) =>
                            t.unit === current &&
                            (t.sees_all || RULES[t.id]?.includes(key) || t.groups.includes(groupOf[key])),
                    )
                    .map((t) => t.name)
                    .sort()
            return {
                units,
                unit: current,
                dashboards: catalog.available
                    .filter((d) => d.units.includes(current))
                    .map((d) => ({
                        key: d.key,
                        title: d.title,
                        area: d.area,
                        group: groupOf[d.key],
                        teams: teamsOf(d.key),
                    })),
                groups: HUB_GROUPS,
                teams,
                roles: ROLES,
                rules: data.teams.flatMap((t) =>
                    (RULES[t.id] ?? [])
                        .filter((key) => keysOf(t.unit).includes(key))
                        .map((key) => ({ team_id: t.id, dashboard_key: key })),
                ),
                dashboards_by_unit: Object.fromEntries(units.map((u) => [u.code, keysOf(u.code)])),
                titles: Object.fromEntries(catalog.available.map((d) => [d.key, d.title])),
                group_of: groupOf,
                can_set_org_role: true,
            }
        },

        update(id: string, update: MemberAccessUpdate, selfEmail: string): Member {
            const data = members.list()
            const member = data.members.find((m) => m.id === id)
            if (!member) throw new DataError(403, 'Você não gere o acesso desta pessoa.')
            if (member.status === 'disabled') throw new DataError(409, 'Reative a pessoa antes de mudar o acesso.')
            if (update.org_role && update.org_role !== member.org_role) {
                if (member.org_role === 'owner') throw new DataError(409, 'O Owner não muda de papel por aqui.')
                if (member.email === selfEmail) throw new DataError(409, 'Você não pode mudar o seu próprio papel.')
            }
            if (update.units.some((u) => !UNIT_ROLES.includes(u.role as UnitRoleKey))) {
                throw new DataError(409, 'Cargo inválido.')
            }
            const withRole = new Set(update.units.map((u) => u.code))
            if (data.teams.some((t) => update.teams.includes(t.id) && !withRole.has(t.unit))) {
                throw new DataError(409, 'Equipe sem cargo na unidade.')
            }
            if (update.extra_groups.some((g) => !withRole.has(g.unit))) {
                throw new DataError(409, 'Grupo extra sem cargo na unidade.')
            }
            if (update.extra_groups.some((g) => !isGroup(g.slug))) throw new DataError(409, 'Grupo inválido.')
            if (update.extra_dashboards.some((d) => !withRole.has(d.unit))) {
                throw new DataError(409, 'Dashboard avulso sem cargo na unidade.')
            }
            if (update.extra_dashboards.some((d) => !keysOf(d.unit).includes(d.key))) {
                throw new DataError(409, 'Dashboard avulso não existe nesta unidade.')
            }
            return members.setAccess(id, update)
        },

        setTeamGroups(teamId: string, groups: string[], seesAllFlag: boolean | null): void {
            if (!members.list().teams.some((t) => t.id === teamId))
                throw new DataError(403, 'Você não gere esta equipe.')
            if (groups.some((g) => !isGroup(g))) throw new DataError(409, 'Grupo inválido.')
            teamGroups[teamId] = [...new Set(groups)].sort()
            if (seesAllFlag === true) seesAll.add(teamId)
            if (seesAllFlag === false) seesAll.delete(teamId)
        },
    }
}
