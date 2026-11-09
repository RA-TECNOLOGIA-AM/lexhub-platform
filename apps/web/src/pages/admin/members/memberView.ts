import type { Member, MemberStatus, RoleKey } from '../../../types/index.ts'

export const ROLE_LABEL: Record<RoleKey, string> = {
    owner: 'Owner',
    admin: 'Admin',
    gestor: 'Gestor',
    colaborador: 'Colaborador',
    leitor: 'Leitor',
}

const STATUS: Record<MemberStatus, { label: string; badge: string }> = {
    active: { label: 'Ativo', badge: 'badge ok' },
    invited: { label: 'Convite pendente', badge: 'badge warn' },
    requested: { label: 'Aguardando aprovação', badge: 'badge info' },
    disabled: { label: 'Desativado', badge: 'badge neutral' },
}

export const statusOf = (m: Member) => STATUS[m.status]

export const roleOf = (m: Member) => ({
    label: m.role ? ROLE_LABEL[m.role] : 'Sem papel',
    badge: m.role === 'admin' || m.role === 'owner' ? 'badge pro' : 'badge neutral',
})

// "NG, LA AM · Comercial" · "Todas as unidades · Diretoria" · "Sem equipe nem unidade"
export function scopeOf(m: Member): string {
    if (m.units.length === 0 && !m.team) return 'Sem equipe nem unidade'
    const units = m.units.includes('*') ? 'Todas as unidades' : m.units.map((u) => u.replace('_', ' ')).join(', ')
    return [units, m.team].filter(Boolean).join(' · ')
}

// Iniciais do nome, ou das duas primeiras letras do e-mail quando ainda não há nome.
export function initialsOf(m: Member): string {
    const base = m.name ?? m.email
    const parts = base.split(/[\s@.]+/).filter(Boolean)
    return ((parts[0]?.[0] ?? '') + (parts[1]?.[0] ?? '')).toUpperCase()
}

// Quem ainda não entrou (convite ou pedido) tem o avatar amarelo.
export const isWaiting = (m: Member) => m.status === 'invited' || m.status === 'requested'

// --- Filtros (Buscar, Unidade, Papel) ---
export type MemberFilter = { q: string; unit: string; role: RoleKey | '' } // '' = todas / todos

// "Fernánda" e "fernanda" são iguais na busca.
const normalize = (text: string) =>
    text
        .normalize('NFD')
        .replace(/\p{Diacritic}/gu, '')
        .toLowerCase()

export function filterMembers(list: Member[], f: MemberFilter): Member[] {
    const q = normalize(f.q.trim())
    return list.filter(
        (m) =>
            (!q || normalize(`${m.name ?? ''} ${m.email}`).includes(q)) &&
            (!f.unit || m.units.includes('*') || m.units.includes(f.unit)) &&
            (!f.role || m.role === f.role),
    )
}

// Filtro <-> URL (?busca=&unidade=&papel=). Papel desconhecido na URL vira "todos".
export function filterFromParams(params: URLSearchParams): MemberFilter {
    const role = params.get('papel') ?? ''
    return {
        q: params.get('busca') ?? '',
        unit: params.get('unidade') ?? '',
        role: role in ROLE_LABEL ? (role as RoleKey) : '',
    }
}

export function paramsFromFilter(f: MemberFilter): URLSearchParams {
    const params = new URLSearchParams()
    if (f.q) params.set('busca', f.q)
    if (f.unit) params.set('unidade', f.unit)
    if (f.role) params.set('papel', f.role)
    return params
}
