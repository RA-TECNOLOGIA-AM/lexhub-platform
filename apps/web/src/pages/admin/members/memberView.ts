import type {
    Invitation,
    Member,
    MembersResponse,
    MemberTeam,
    OrgRoleKey,
    Unit,
    UnitRoleKey,
} from '../../../types/index.ts'
import { matchesText } from '../../../lib/text.ts'

// Regras da lista de Membros (sem React); os testes ficam em memberView.test.ts.

export const ROLE_LABEL: Record<OrgRoleKey | UnitRoleKey, string> = {
    owner: 'Owner',
    admin: 'Desenvolvedor',
    member: 'Membro',
    gestor: 'Gestor',
    controller: 'Controller',
    colaborador: 'Colaborador',
    leitor: 'Leitor',
}

// Do maior para o menor (o que aparece com "Todas as unidades").
const UNIT_ROLE_ORDER: UnitRoleKey[] = ['gestor', 'controller', 'colaborador', 'leitor']

// Uma linha da tabela: um membro ou um convite pendente.
export type MemberRow = { kind: 'member'; member: Member } | { kind: 'invitation'; invitation: Invitation }

export const rowKey = (row: MemberRow) => (row.kind === 'member' ? row.member.id : `convite-${row.invitation.id}`)

// Membros na ordem do servidor e, depois, os convites pendentes.
export function rowsOf(data: MembersResponse): MemberRow[] {
    return [
        ...data.members.map((member): MemberRow => ({ kind: 'member', member })),
        ...data.invitations.map((invitation): MemberRow => ({ kind: 'invitation', invitation })),
    ]
}

export const activeCount = (data: MembersResponse) => data.members.filter((m) => m.status === 'active').length

const isOrgWide = (m: Member) => m.org_role === 'owner' || m.org_role === 'admin'
const unitLabel = (code: string) => code.replace('_', ' ')

// unit = a unidade escolhida no seletor (null = todas).
export function roleOf(row: MemberRow, unit: string | null): { label: string; badge: string } {
    if (row.kind === 'invitation') {
        const role = row.invitation.role
        return { label: ROLE_LABEL[role], badge: role === 'admin' ? 'badge pro' : 'badge neutral' }
    }
    const m = row.member
    if (isOrgWide(m)) return { label: ROLE_LABEL[m.org_role], badge: 'badge pro' }
    if (unit) {
        const here = m.units.find((u) => u.code === unit)
        return { label: here ? ROLE_LABEL[here.role] : 'Sem cargo aqui', badge: 'badge neutral' }
    }
    const top = UNIT_ROLE_ORDER.find((r) => m.units.some((u) => u.role === r))
    if (!top) return { label: 'Sem cargo', badge: 'badge neutral' }
    const others = m.units.length - 1
    return { label: others > 0 ? `${ROLE_LABEL[top]} +${others}` : ROLE_LABEL[top], badge: 'badge neutral' }
}

// "LA AM, NG · Comercial" · "Todas as unidades · Diretoria" · "Sem unidade nem equipe"
export function scopeOf(row: MemberRow): string {
    const [units, teams] =
        row.kind === 'member'
            ? [
                  isOrgWide(row.member)
                      ? 'Todas as unidades'
                      : row.member.units.map((u) => unitLabel(u.code)).join(', '),
                  row.member.teams,
              ]
            : [
                  row.invitation.role === 'admin'
                      ? 'Todas as unidades'
                      : row.invitation.units.map(unitLabel).join(', '),
                  row.invitation.teams,
              ]
    const text = [units, teams.join(', ')].filter(Boolean).join(' · ')
    return text || 'Sem unidade nem equipe'
}

const STATUS: Record<Member['status'], { label: string; badge: string }> = {
    active: { label: 'Ativo', badge: 'badge ok' },
    invited: { label: 'Convite pendente', badge: 'badge warn' },
    disabled: { label: 'Desativado', badge: 'badge neutral' },
}

export const statusOf = (row: MemberRow) => STATUS[row.kind === 'member' ? row.member.status : 'invited']

// "Ver como este membro" (modo suporte): só quem tem a permissão (Owner/Dev), só membro ativo, nunca a si mesmo.
// O servidor confere de novo ao iniciar; aqui só decide se o botão aparece.
export const canViewAs = (row: MemberRow, canSupport: boolean, isSelf: boolean): boolean =>
    canSupport && !isSelf && row.kind === 'member' && row.member.status === 'active'

// Linha de baixo: o e-mail do membro, ou quem convidou e quando o convite vence.
export function noteOf(row: MemberRow, now: Date): string {
    if (row.kind === 'member') return row.member.email
    const { invited_by, expires_at } = row.invitation
    // Menos de 24 h = "hoje"; senão arredonda para cima (convite de agora = "7 dias", não 6).
    const DAY = 24 * 60 * 60 * 1000
    const left = new Date(expires_at).getTime() - now.getTime()
    const days = Math.ceil(left / DAY)
    const due = left < DAY ? 'vence hoje' : `vence em ${days} ${days === 1 ? 'dia' : 'dias'}`
    return invited_by ? `Convidado por ${invited_by} · ${due}` : `Convite · ${due}`
}

export const nameOf = (row: MemberRow) => (row.kind === 'member' ? row.member.name : row.invitation.email)

// Iniciais do nome (ou das duas primeiras partes do e-mail, no convite).
export function initialsOf(row: MemberRow): string {
    const parts = nameOf(row)
        .split(/[\s@.]+/)
        .filter(Boolean)
    return ((parts[0]?.[0] ?? '') + (parts[1]?.[0] ?? '')).toUpperCase()
}

// --- Filtros (Buscar, Unidade, Cargo, Situação) ---
export type MemberStatusFilter = Member['status'] | '' // '' = todas
export type MemberFilter = {
    q: string
    unit: string
    role: OrgRoleKey | UnitRoleKey | '' // '' = todas / todos
    status: MemberStatusFilter
}

export const STATUS_OPTIONS: { value: Member['status']; label: string }[] = [
    { value: 'active', label: 'Ativo' },
    { value: 'invited', label: 'Convite pendente' },
    { value: 'disabled', label: 'Desativado' },
]

function inUnit(row: MemberRow, unit: string): boolean {
    if (row.kind === 'invitation') return row.invitation.role === 'admin' || row.invitation.units.includes(unit)
    return isOrgWide(row.member) || row.member.units.some((u) => u.code === unit)
}

function hasRole(row: MemberRow, role: MemberFilter['role'], unit: string): boolean {
    if (row.kind === 'invitation') return row.invitation.role === role
    const m = row.member
    return m.org_role === role || m.units.some((u) => u.role === role && (!unit || u.code === unit))
}

const statusKey = (row: MemberRow) => (row.kind === 'member' ? row.member.status : 'invited')

export function filterRows(rows: MemberRow[], f: MemberFilter): MemberRow[] {
    return rows.filter((row) => {
        // Busca por nome, e-mail ou setor.
        const text =
            row.kind === 'member'
                ? `${row.member.name} ${row.member.email} ${row.member.teams.join(' ')}`
                : `${row.invitation.email} ${row.invitation.teams.join(' ')}`
        return (
            matchesText(text, f.q) &&
            (!f.unit || inUnit(row, f.unit)) &&
            (!f.role || hasRole(row, f.role, f.unit)) &&
            (!f.status || statusKey(row) === f.status)
        )
    })
}

// Filtro <-> URL (?busca=&unidade=&papel=&situacao=). Valor desconhecido na URL vira "todos".
export function filterFromParams(params: URLSearchParams): MemberFilter {
    const role = params.get('papel') ?? ''
    return {
        q: params.get('busca') ?? '',
        unit: params.get('unidade') ?? '',
        role: role in ROLE_LABEL ? (role as MemberFilter['role']) : '',
        status: STATUS_OPTIONS.find((o) => o.value === params.get('situacao'))?.value ?? '',
    }
}

export function paramsFromFilter(f: MemberFilter): URLSearchParams {
    const params = new URLSearchParams()
    if (f.q) params.set('busca', f.q)
    if (f.unit) params.set('unidade', f.unit)
    if (f.role) params.set('papel', f.role)
    if (f.status) params.set('situacao', f.status)
    return params
}

// --- Mestre-detalhe (lista à esquerda, pessoa à direita) ---

// O que a pessoa tem numa unidade (só leitura): cargo, setores e exceções (só visualizam).
export type UnitView = { role: string | null; sectors: string[]; extraGroups: number; extraDashboards: number }

export function unitViewOf(row: MemberRow, unit: string, teams: MemberTeam[]): UnitView {
    if (row.kind === 'invitation') {
        const i = row.invitation
        const inUnit = i.role === 'admin' || i.units.includes(unit)
        const sectors = teams.filter((t) => t.unit === unit && i.teams.includes(t.name)).map((t) => t.name)
        return { role: inUnit ? ROLE_LABEL[i.role] : null, sectors, extraGroups: 0, extraDashboards: 0 }
    }
    const m = row.member
    const here = m.units.find((u) => u.code === unit)
    return {
        role: here ? ROLE_LABEL[here.role] : null,
        sectors: teams.filter((t) => t.unit === unit && m.team_ids.includes(t.id)).map((t) => t.name),
        extraGroups: m.extra_groups.filter((g) => g.unit === unit).length,
        extraDashboards: m.extra_dashboards.filter((d) => d.unit === unit).length,
    }
}

// Bolinha acesa na aba: a pessoa tem algo nesta unidade.
export const hasUnitAccess = (v: UnitView) =>
    v.role !== null || v.sectors.length > 0 || v.extraGroups > 0 || v.extraDashboards > 0

// Primeira unidade com algo; senão a primeira da lista.
export function firstUnitOf(row: MemberRow, units: string[], teams: MemberTeam[]): string {
    return units.find((u) => hasUnitAccess(unitViewOf(row, u, teams))) ?? units[0] ?? ''
}

// --- Lista em pílulas (uma linha por pessoa) ---

// "LUIS ALBERT AM, NICOLAS GOMES" · "TODAS" (Owner/Dev) · "—"
export function unitsText(row: MemberRow, units: Unit[]): string {
    const name = (code: string) => (units.find((u) => u.code === code)?.name ?? unitLabel(code)).toUpperCase()
    if (row.kind === 'invitation') {
        if (row.invitation.role === 'admin') return 'TODAS'
        return row.invitation.units.map(name).join(', ') || '—'
    }
    if (isOrgWide(row.member)) return 'TODAS'
    return row.member.units.map((u) => name(u.code)).join(', ') || '—'
}

export const sectorsText = (row: MemberRow) =>
    (row.kind === 'member' ? row.member.teams : row.invitation.teams).join(', ') || '—'

// --- Presença: quem está com o LexHub aberto avisa a cada minuto (usePresenceHeartbeat) ---
// Sem aviso há mais que isso: deixa de estar online (folga para um aviso atrasado ou perdido).
export const ONLINE_MS = 3 * 60_000
const MINUTE = 60_000
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

export const isOnline = (row: MemberRow, now: Date): boolean =>
    row.kind === 'member' &&
    row.member.status === 'active' &&
    !!row.member.last_seen_at &&
    now.getTime() - new Date(row.member.last_seen_at).getTime() < ONLINE_MS

// "Online agora" · "Visto há 12 min" · "Visto há 3 h" · "Visto há 2 dias" · "Visto em 05/10/2026" (30+ dias)
// · "Nunca acessou" (convite ou sem registro).
export function lastSeenText(row: MemberRow, now: Date): string {
    if (row.kind === 'invitation' || !row.member.last_seen_at) return 'Nunca acessou'
    if (isOnline(row, now)) return 'Online agora'
    const seen = new Date(row.member.last_seen_at)
    const ago = Math.max(0, now.getTime() - seen.getTime())
    if (ago < HOUR) return `Visto há ${Math.max(1, Math.floor(ago / MINUTE))} min`
    if (ago < DAY) return `Visto há ${Math.floor(ago / HOUR)} h`
    const days = Math.floor(ago / DAY)
    if (days < 30) return `Visto há ${days} ${days === 1 ? 'dia' : 'dias'}`
    return `Visto em ${seen.toLocaleDateString('pt-BR')}`
}

// --- Como a lista aparece (pílulas ou cards), lembrado no localStorage deste navegador ---
export type MembersLayout = 'cards' | 'pilulas'
export const MEMBERS_LAYOUT_KEY = 'lexhub.membersLayout'

// Sem escolha, valor estranho ou storage bloqueado: cards.
export function storedMembersLayout(storage: Pick<Storage, 'getItem'> | null = safeLocal()): MembersLayout {
    try {
        return storage?.getItem(MEMBERS_LAYOUT_KEY) === 'pilulas' ? 'pilulas' : 'cards'
    } catch {
        return 'cards'
    }
}

export function storeMembersLayout(layout: MembersLayout, storage: Pick<Storage, 'setItem'> | null = safeLocal()) {
    try {
        storage?.setItem(MEMBERS_LAYOUT_KEY, layout)
    } catch {
        // sem storage: vale só enquanto a página estiver aberta
    }
}

function safeLocal(): Storage | null {
    try {
        return window.localStorage
    } catch {
        return null
    }
}
