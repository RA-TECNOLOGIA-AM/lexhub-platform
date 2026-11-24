import { describeUserAgent } from '../../services/userAgent.ts'
import type { AccountSession } from '../../types/index.ts'

export type DeviceKind = 'computer' | 'phone' | 'tv'

// Um aparelho na lista de Dispositivos: uma ou mais sessões (vários logins do mesmo navegador e IP).
export type DeviceGroup = {
    key: string
    ids: string[]
    label: string // 'Chrome · Windows', 'TV (QR)' ou 'Aparelho desconhecido'
    ip: string | null
    kind: DeviceKind
    lastActiveAt: string // a mais recente do grupo
    current: boolean // este aparelho (sempre sozinho no grupo)
}

const PHONE = /Android|iPhone|iPad|iPod/

// Que ícone mostrar: TV (login pelo QR), celular ou computador (o resto, inclusive desconhecido).
export function deviceKind(ua: string | null): DeviceKind {
    if (describeUserAgent(ua) === 'TV (QR)') return 'tv'
    return ua && PHONE.test(ua) ? 'phone' : 'computer'
}

// Módulo: transforma as sessões da conta nas linhas da tela. A atual vem primeiro e sozinha; as outras
// se juntam por IP + navegador/sistema e vêm da atividade mais recente para a mais antiga.
export function groupSessions(sessions: AccountSession[]): DeviceGroup[] {
    const current: DeviceGroup[] = []
    const others = new Map<string, DeviceGroup>()
    for (const s of sessions) {
        const label = describeUserAgent(s.userAgent) ?? 'Aparelho desconhecido'
        const base = { ip: s.ip, label, kind: deviceKind(s.userAgent), lastActiveAt: s.lastActiveAt }
        if (s.current) {
            current.push({ ...base, key: s.id, ids: [s.id], current: true })
            continue
        }
        const key = `${s.ip ?? ''}|${label}`
        const group = others.get(key)
        if (!group) {
            others.set(key, { ...base, key, ids: [s.id], current: false })
            continue
        }
        group.ids.push(s.id)
        if (Date.parse(s.lastActiveAt) > Date.parse(group.lastActiveAt)) group.lastActiveAt = s.lastActiveAt
    }
    const rest = [...others.values()].sort((a, b) => Date.parse(b.lastActiveAt) - Date.parse(a.lastActiveAt))
    return [...current, ...rest]
}
