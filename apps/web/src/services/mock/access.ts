import { DataError } from '../errors.ts'
import type { AccessOverview, Member, MemberAccessUpdate, UnitRoleKey } from '../../types/index.ts'
import { catalog } from './catalog.ts'
import type { createMembersStore } from './members.ts'

// Regras das equipes do mock (team_id -> dashboards que liberam), como app.access_rules.
// Diretoria (NG) libera todos os dashboards da unidade, como no banco (uma regra por dashboard).
const NG_KEYS = catalog.available.filter((d) => d.units.includes('NG')).map((d) => d.key)
const RULES: Record<string, string[]> = {
    't-protocolo': ['protocolo-lexpre', 'pendencias-lexpre', 'peticionamento-lexpre', 'pre-protocolo'],
    't-comercial': ['comercial-lexpre', 'comissao-lexpre', 'nps'],
    't-diretoria': NG_KEYS,
    't-pendencias': ['pendencias', 'pendencias-lexpre'],
}

// O que cada cargo faz (app.role_permissions): Gestor e Controller veem tudo da unidade; Leitor não exporta.
const ROLES: AccessOverview['roles'] = [
    { key: 'gestor', sees_all: true, exports: true },
    { key: 'controller', sees_all: true, exports: true },
    { key: 'colaborador', sees_all: false, exports: true },
    { key: 'leitor', sees_all: false, exports: false },
]
const UNIT_ROLES = ROLES.map((r) => r.key)

const keysOf = (unit: string) => catalog.available.filter((d) => d.units.includes(unit)).map((d) => d.key)

// Módulo: o Acesso do mock, com as mesmas regras e mensagens de api.access_overview e
// api.update_member_access. O mock é Owner/Desenvolvedor: gere todas as unidades.
// Parâmetro: a loja de Membros (editar acesso muda a lista de Membros também).
export function createAccessStore(members: ReturnType<typeof createMembersStore>) {
    return {
        overview(unit: string | null): AccessOverview {
            const data = members.list()
            const units = [...data.units].sort((a, b) => a.code.localeCompare(b.code))
            const current = unit ?? units[0]?.code
            if (!units.some((u) => u.code === current)) throw new DataError(403, 'Você não gere acesso nesta unidade.')
            const teamsOf = (key: string) =>
                data.teams
                    .filter((t) => t.unit === current && RULES[t.id]?.includes(key))
                    .map((t) => t.name)
                    .sort()
            return {
                units,
                unit: current,
                dashboards: catalog.available
                    .filter((d) => d.units.includes(current))
                    .map((d) => ({ key: d.key, title: d.title, area: d.area, teams: teamsOf(d.key) })),
                teams: data.teams,
                roles: ROLES,
                rules: data.teams.flatMap((t) =>
                    (RULES[t.id] ?? [])
                        .filter((key) => keysOf(t.unit).includes(key))
                        .map((key) => ({ team_id: t.id, dashboard_key: key })),
                ),
                dashboards_by_unit: Object.fromEntries(units.map((u) => [u.code, keysOf(u.code)])),
                titles: Object.fromEntries(catalog.available.map((d) => [d.key, d.title])),
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
            return members.setAccess(id, update)
        },
    }
}
