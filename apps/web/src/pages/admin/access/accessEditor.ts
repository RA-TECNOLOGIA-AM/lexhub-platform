import type {
    AccessOverview,
    AccessTeam,
    Member,
    MemberAccessUpdate,
    MemberTeam,
    OrgRoleKey,
    UnitRoleKey,
} from '../../../types/index.ts'

// Regras do editor de acesso (sem React); os testes ficam em accessEditor.test.ts.

// O que está sendo editado: papel na org, cargo por unidade gerida ('' = sem cargo), equipes (ids)
// e as exceções da pessoa por unidade (grupos extras e dashboards avulsos: só visualização).
export type AccessDraft = {
    orgRole: OrgRoleKey
    units: Record<string, UnitRoleKey | ''>
    teams: string[]
    extraGroups: Record<string, string[]> // unidade -> slugs
    extraDashboards: Record<string, string[]> // unidade -> keys
}

function byUnit<T extends { unit: string }>(items: T[], units: string[], pick: (item: T) => string) {
    return Object.fromEntries(units.map((u) => [u, items.filter((i) => i.unit === u).map(pick)]))
}

export function draftFromMember(m: Member, overview: AccessOverview): AccessDraft {
    const managed = new Set(overview.teams.map((t) => t.id))
    const codes = overview.units.map((u) => u.code)
    return {
        orgRole: m.org_role,
        units: Object.fromEntries(
            overview.units.map((u) => [u.code, m.units.find((mu) => mu.code === u.code)?.role ?? '']),
        ),
        teams: m.team_ids.filter((id) => managed.has(id)),
        extraGroups: byUnit(m.extra_groups, codes, (g) => g.slug),
        extraDashboards: byUnit(m.extra_dashboards, codes, (d) => d.key),
    }
}

// Tirar o cargo de uma unidade tira as equipes e as exceções dela junto (o banco recusa sem cargo).
export function setUnitRole(
    draft: AccessDraft,
    unit: string,
    role: UnitRoleKey | '',
    teams: MemberTeam[],
): AccessDraft {
    if (role) return { ...draft, units: { ...draft.units, [unit]: role } }
    const unitTeams = new Set(teams.filter((t) => t.unit === unit).map((t) => t.id))
    return {
        ...draft,
        units: { ...draft.units, [unit]: role },
        teams: draft.teams.filter((id) => !unitTeams.has(id)),
        extraGroups: { ...draft.extraGroups, [unit]: [] },
        extraDashboards: { ...draft.extraDashboards, [unit]: [] },
    }
}

const toggle = (list: string[], item: string) =>
    list.includes(item) ? list.filter((x) => x !== item) : [...list, item]

export function toggleTeam(draft: AccessDraft, id: string): AccessDraft {
    return { ...draft, teams: toggle(draft.teams, id) }
}

export function toggleExtraGroup(draft: AccessDraft, unit: string, slug: string): AccessDraft {
    return { ...draft, extraGroups: { ...draft.extraGroups, [unit]: toggle(draft.extraGroups[unit] ?? [], slug) } }
}

export function toggleExtraDashboard(draft: AccessDraft, unit: string, key: string): AccessDraft {
    return {
        ...draft,
        extraDashboards: { ...draft.extraDashboards, [unit]: toggle(draft.extraDashboards[unit] ?? [], key) },
    }
}

const sameSet = (a: string[], b: string[]) => a.length === b.length && a.every((x) => b.includes(x))

export function isDirty(original: AccessDraft, draft: AccessDraft): boolean {
    const units = Object.keys(draft.units)
    return (
        original.orgRole !== draft.orgRole ||
        !sameSet(original.teams, draft.teams) ||
        units.some((u) => (original.units[u] ?? '') !== draft.units[u]) ||
        units.some((u) => !sameSet(original.extraGroups[u] ?? [], draft.extraGroups[u] ?? [])) ||
        units.some((u) => !sameSet(original.extraDashboards[u] ?? [], draft.extraDashboards[u] ?? []))
    )
}

// O que vai para api.update_member_access. org_role só quando mudou e quem salva pode mudar.
// Exceções só das unidades com cargo (as outras o banco recusa e, sem cargo, apaga).
export function toUpdate(draft: AccessDraft, original: AccessDraft, canSetOrgRole: boolean): MemberAccessUpdate {
    const changedRole = canSetOrgRole && draft.orgRole !== original.orgRole && draft.orgRole !== 'owner'
    const withRole = Object.keys(draft.units).filter((u) => draft.units[u] !== '')
    return {
        units: Object.entries(draft.units)
            .filter((entry): entry is [string, UnitRoleKey] => entry[1] !== '')
            .map(([code, role]) => ({ code, role })),
        teams: draft.teams,
        org_role: changedRole ? (draft.orgRole as 'admin' | 'member') : null,
        extra_groups: withRole.flatMap((unit) => (draft.extraGroups[unit] ?? []).map((slug) => ({ unit, slug }))),
        extra_dashboards: withRole.flatMap((unit) => (draft.extraDashboards[unit] ?? []).map((key) => ({ unit, key }))),
    }
}

const isOrgWide = (role: OrgRoleKey) => role === 'owner' || role === 'admin'

// O que os setores marcados liberam numa unidade (camadas 1 e 2): tudo (setor que vê tudo),
// colunas inteiras (grupo -> setores que dão) e cards avulsos do setor.
export type SectorCoverage = { all: boolean; groups: Map<string, string[]>; keys: Set<string> }

export function sectorCoverage(overview: AccessOverview, draft: AccessDraft, unit: string): SectorCoverage {
    const mine: AccessTeam[] = overview.teams.filter((t) => t.unit === unit && draft.teams.includes(t.id))
    const groups = new Map<string, string[]>()
    for (const t of mine) for (const g of t.groups) groups.set(g, [...(groups.get(g) ?? []), t.name])
    const ids = new Set(mine.map((t) => t.id))
    return {
        all: mine.some((t) => t.sees_all),
        groups,
        keys: new Set(overview.rules.filter((r) => ids.has(r.team_id)).map((r) => r.dashboard_key)),
    }
}

// Cargo que vê tudo da unidade (Gestor, Controller): as exceções não fazem diferença.
export function roleSeesAll(overview: AccessOverview, role: UnitRoleKey | ''): boolean {
    return role !== '' && overview.roles.some((r) => r.key === role && r.sees_all)
}

// O que a pessoa passa a ver, por unidade — a mesma regra de app_private.dashboard_access:
// Owner/Desenvolvedor veem tudo; cargo com sees_all (Gestor, Controller) vê tudo da unidade;
// os demais veem o que os setores deles NAQUELA unidade liberam (titles) somado às exceções
// da pessoa na unidade (personal: só visualiza).
export type UnitPreview = {
    unit: string
    all: boolean
    titles: string[] // pelo cargo ou pelo setor
    personal: string[] // exceção da pessoa (só visualiza)
    total: number // ligados na unidade
}

export function previewDashboards(overview: AccessOverview, draft: AccessDraft): UnitPreview[] {
    const titlesOf = (keys: string[]) => keys.map((k) => overview.titles[k] ?? k)
    return overview.units.flatMap((u): UnitPreview[] => {
        const keys = overview.dashboards_by_unit[u.code] ?? []
        const everything = { unit: u.code, all: true, titles: titlesOf(keys), personal: [], total: keys.length }
        if (isOrgWide(draft.orgRole)) return [everything]
        const role = draft.units[u.code]
        if (!role) return []
        if (roleSeesAll(overview, role)) return [everything]
        const cov = sectorCoverage(overview, draft, u.code)
        if (cov.all) return [everything]
        const bySector = (k: string) => cov.keys.has(k) || cov.groups.has(overview.group_of[k])
        const groups = draft.extraGroups[u.code] ?? []
        const avulsos = draft.extraDashboards[u.code] ?? []
        const byPerson = (k: string) => groups.includes(overview.group_of[k]) || avulsos.includes(k)
        return [
            {
                unit: u.code,
                all: false,
                titles: titlesOf(keys.filter(bySector)),
                personal: titlesOf(keys.filter((k) => !bySector(k) && byPerson(k))),
                total: keys.length,
            },
        ]
    })
}

// Dashboards que ainda podem virar avulsos numa unidade: ligados nela e não cobertos pelos setores
// marcados nem pelos grupos extras. covered = quantos ficaram de fora por já estarem cobertos.
export function avulsoOptions(
    overview: AccessOverview,
    draft: AccessDraft,
    unit: string,
): { options: { key: string; title: string; group: string }[]; covered: number } {
    const keys = overview.dashboards_by_unit[unit] ?? []
    const cov = sectorCoverage(overview, draft, unit)
    const groups = draft.extraGroups[unit] ?? []
    const isCovered = (k: string) =>
        cov.all || cov.keys.has(k) || cov.groups.has(overview.group_of[k]) || groups.includes(overview.group_of[k])
    const order = overview.groups.map((g) => g.slug)
    const options = keys
        .filter((k) => !isCovered(k))
        .map((k) => ({ key: k, title: overview.titles[k] ?? k, group: overview.group_of[k] ?? '' }))
        .sort((a, b) => order.indexOf(a.group) - order.indexOf(b.group)) // estável: mantém a ordem do hub
    return { options, covered: keys.length - options.length }
}

// A frase da prévia de uma unidade ("todos os 12 dashboards", "2 de 12: Protocolo, Pendências"...).
export function previewText(p: UnitPreview): string {
    if (p.total === 0) return 'nenhum dashboard ligado nesta unidade'
    if (p.all) return `todos os ${p.total} dashboards`
    const seen = p.titles.length + p.personal.length
    if (seen === 0) return 'nenhum — marque um setor, um grupo extra ou um dashboard avulso'
    if (p.titles.length === 0) return `${seen} de ${p.total}`
    return `${seen} de ${p.total}: ${p.titles.join(', ')}`
}

// A linha das exceções na prévia ('' = nenhuma).
export function personalText(p: UnitPreview): string {
    return p.personal.length ? `só visualiza (exceção): ${p.personal.join(', ')}` : ''
}

// Por que a janela abre só para ver (null = pode editar). As mesmas regras de api.update_member_access:
// quem não é Owner/Desenvolvedor não mexe em Owner/Desenvolvedor nem no próprio acesso.
export function readOnlyReason(member: Member, overview: AccessOverview, isSelf: boolean): string | null {
    if (overview.can_set_org_role) return null
    if (member.org_role === 'owner' || member.org_role === 'admin') {
        return 'Owner e Desenvolvedor: só Owner ou Desenvolvedor muda o acesso desta pessoa.'
    }
    if (isSelf) return 'Você não muda o próprio acesso: peça ao Owner ou a um Desenvolvedor.'
    return null
}

// Uma célula da grade "o que cada cargo vê" (unidade da overview).
export type GridCell = { kind: 'all' } | { kind: 'teams'; teams: string[] } | { kind: 'none' }

export function gridCell(overview: AccessOverview, key: string, role: UnitRoleKey): GridCell {
    if (overview.roles.find((r) => r.key === role)?.sees_all) return { kind: 'all' }
    const teams = overview.dashboards.find((d) => d.key === key)?.teams ?? []
    return teams.length ? { kind: 'teams', teams } : { kind: 'none' }
}
