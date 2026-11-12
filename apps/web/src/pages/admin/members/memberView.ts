import type { Invitation, Member, MembersResponse, OrgRoleKey, UnitRoleKey } from '../../../types/index.ts'
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

// --- Filtros (Buscar, Unidade, Papel) ---
export type MemberFilter = { q: string; unit: string; role: OrgRoleKey | UnitRoleKey | '' } // '' = todas / todos

function inUnit(row: MemberRow, unit: string): boolean {
    if (row.kind === 'invitation') return row.invitation.role === 'admin' || row.invitation.units.includes(unit)
    return isOrgWide(row.member) || row.member.units.some((u) => u.code === unit)
}

function hasRole(row: MemberRow, role: MemberFilter['role'], unit: string): boolean {
    if (row.kind === 'invitation') return row.invitation.role === role
    const m = row.member
    return m.org_role === role || m.units.some((u) => u.role === role && (!unit || u.code === unit))
}

export function filterRows(rows: MemberRow[], f: MemberFilter): MemberRow[] {
    return rows.filter((row) => {
        const text = row.kind === 'member' ? `${row.member.name} ${row.member.email}` : row.invitation.email
        return matchesText(text, f.q) && (!f.unit || inUnit(row, f.unit)) && (!f.role || hasRole(row, f.role, f.unit))
    })
}

// Filtro <-> URL (?busca=&unidade=&papel=). Papel desconhecido na URL vira "todos".
export function filterFromParams(params: URLSearchParams): MemberFilter {
    const role = params.get('papel') ?? ''
    return {
        q: params.get('busca') ?? '',
        unit: params.get('unidade') ?? '',
        role: role in ROLE_LABEL ? (role as MemberFilter['role']) : '',
    }
}

export function paramsFromFilter(f: MemberFilter): URLSearchParams {
    const params = new URLSearchParams()
    if (f.q) params.set('busca', f.q)
    if (f.unit) params.set('unidade', f.unit)
    if (f.role) params.set('papel', f.role)
    return params
}
