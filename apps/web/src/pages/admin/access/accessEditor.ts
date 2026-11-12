import type {
    AccessOverview,
    Member,
    MemberAccessUpdate,
    MemberTeam,
    OrgRoleKey,
    UnitRoleKey,
} from '../../../types/index.ts'

// Regras do editor de acesso (sem React); os testes ficam em accessEditor.test.ts.

// O que está sendo editado: papel na org, cargo por unidade gerida ('' = sem cargo) e equipes (ids).
export type AccessDraft = { orgRole: OrgRoleKey; units: Record<string, UnitRoleKey | ''>; teams: string[] }

export function draftFromMember(m: Member, overview: AccessOverview): AccessDraft {
    const managed = new Set(overview.teams.map((t) => t.id))
    return {
        orgRole: m.org_role,
        units: Object.fromEntries(
            overview.units.map((u) => [u.code, m.units.find((mu) => mu.code === u.code)?.role ?? '']),
        ),
        teams: m.team_ids.filter((id) => managed.has(id)),
    }
}

// Tirar o cargo de uma unidade tira as equipes dela junto (o banco recusa equipe sem cargo).
export function setUnitRole(
    draft: AccessDraft,
    unit: string,
    role: UnitRoleKey | '',
    teams: MemberTeam[],
): AccessDraft {
    const unitTeams = new Set(teams.filter((t) => t.unit === unit).map((t) => t.id))
    return {
        ...draft,
        units: { ...draft.units, [unit]: role },
        teams: role ? draft.teams : draft.teams.filter((id) => !unitTeams.has(id)),
    }
}

export function toggleTeam(draft: AccessDraft, id: string): AccessDraft {
    const teams = draft.teams.includes(id) ? draft.teams.filter((t) => t !== id) : [...draft.teams, id]
    return { ...draft, teams }
}

const sameSet = (a: string[], b: string[]) => a.length === b.length && a.every((x) => b.includes(x))

export function isDirty(original: AccessDraft, draft: AccessDraft): boolean {
    return (
        original.orgRole !== draft.orgRole ||
        !sameSet(original.teams, draft.teams) ||
        Object.keys(draft.units).some((u) => (original.units[u] ?? '') !== draft.units[u])
    )
}

// O que vai para api.update_member_access. org_role só quando mudou e quem salva pode mudar.
export function toUpdate(draft: AccessDraft, original: AccessDraft, canSetOrgRole: boolean): MemberAccessUpdate {
    const changedRole = canSetOrgRole && draft.orgRole !== original.orgRole && draft.orgRole !== 'owner'
    return {
        units: Object.entries(draft.units)
            .filter((entry): entry is [string, UnitRoleKey] => entry[1] !== '')
            .map(([code, role]) => ({ code, role })),
        teams: draft.teams,
        org_role: changedRole ? (draft.orgRole as 'admin' | 'member') : null,
    }
}

const isOrgWide = (role: OrgRoleKey) => role === 'owner' || role === 'admin'

// O que a pessoa passa a ver, por unidade — a mesma regra de app_private.dashboard_scope:
// Owner/Desenvolvedor veem tudo; cargo com sees_all (Gestor, Controller) vê tudo da unidade;
// os demais veem o que alguma equipe deles NAQUELA unidade libera.
export type UnitPreview = { unit: string; all: boolean; titles: string[]; total: number } // total = ligados na unidade

export function previewDashboards(overview: AccessOverview, draft: AccessDraft): UnitPreview[] {
    const titlesOf = (keys: string[]) => keys.map((k) => overview.titles[k] ?? k)
    return overview.units.flatMap((u): UnitPreview[] => {
        const keys = overview.dashboards_by_unit[u.code] ?? []
        if (isOrgWide(draft.orgRole)) return [{ unit: u.code, all: true, titles: titlesOf(keys), total: keys.length }]
        const role = draft.units[u.code]
        if (!role) return []
        if (overview.roles.find((r) => r.key === role)?.sees_all) {
            return [{ unit: u.code, all: true, titles: titlesOf(keys), total: keys.length }]
        }
        const myTeams = new Set(
            overview.teams.filter((t) => t.unit === u.code && draft.teams.includes(t.id)).map((t) => t.id),
        )
        const allowed = new Set(overview.rules.filter((r) => myTeams.has(r.team_id)).map((r) => r.dashboard_key))
        return [{ unit: u.code, all: false, titles: titlesOf(keys.filter((k) => allowed.has(k))), total: keys.length }]
    })
}

// A frase da prévia de uma unidade ("todos os 12 dashboards", "2 de 12: Protocolo, Pendências"...).
export function previewText(p: UnitPreview): string {
    if (p.total === 0) return 'nenhum dashboard ligado nesta unidade'
    if (p.all) return `todos os ${p.total} dashboards`
    if (p.titles.length === 0) return 'nenhum — marque uma equipe que libere dashboards'
    return `${p.titles.length} de ${p.total}: ${p.titles.join(', ')}`
}

// Uma célula da grade "o que cada cargo vê" (unidade da overview).
export type GridCell = { kind: 'all' } | { kind: 'teams'; teams: string[] } | { kind: 'none' }

export function gridCell(overview: AccessOverview, key: string, role: UnitRoleKey): GridCell {
    if (overview.roles.find((r) => r.key === role)?.sees_all) return { kind: 'all' }
    const teams = overview.dashboards.find((d) => d.key === key)?.teams ?? []
    return teams.length ? { kind: 'teams', teams } : { kind: 'none' }
}
