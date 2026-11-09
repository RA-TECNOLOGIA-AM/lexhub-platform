import type { ClientPlan, ClientsResponse, PlatformClient } from '../../../types/index.ts'
import { fmt } from '../../../lib/format.ts'

type Badge = { label: string; badge: string }

const PLAN: Record<ClientPlan, Badge> = {
    starter: { label: 'Starter', badge: 'badge neutral' },
    pro: { label: 'Pro', badge: 'badge neutral' },
    enterprise: { label: 'Enterprise', badge: 'badge neutral' },
    onboarding: { label: 'Implantação', badge: 'badge info' },
}

const BILLING: Record<PlatformClient['billing'], Badge> = {
    ok: { label: 'Em dia', badge: 'badge ok' },
    onboarding_paid: { label: 'Implantação paga', badge: 'badge ok' },
    overdue: { label: 'Fatura vencida', badge: 'badge danger' },
}

export const planOf = (c: PlatformClient): Badge => PLAN[c.plan]
export const billingOf = (c: PlatformClient): Badge => BILLING[c.billing]

// Dados: "Saudável" ou "1 fonte atrasada" / "2 fontes atrasadas".
export function dataOf(c: PlatformClient): Badge {
    const n = c.failingSources
    if (n === 0) return { label: 'Saudável', badge: 'badge ok' }
    return { label: n === 1 ? '1 fonte atrasada' : `${n} fontes atrasadas`, badge: 'badge warn' }
}

export type ClientKpis = { active: number; onboarding: number; revenue: string; failingSources: number }

// Os 4 indicadores do topo, calculados da lista (não ficam fixos no mock).
export function kpisOf(data: ClientsResponse): ClientKpis {
    return {
        active: data.clients.length,
        onboarding: data.clients.filter((c) => c.plan === 'onboarding').length,
        revenue: data.monthlyRevenue === null ? 'R$ [—]' : fmt.brl(data.monthlyRevenue),
        failingSources: data.clients.reduce((sum, c) => sum + c.failingSources, 0),
    }
}

// O motivo aparece na auditoria do cliente: precisa existir e dizer alguma coisa.
export const SUPPORT_REASON_MIN = 10

export function validateSupportReason(reason: string): string | null {
    const text = reason.trim()
    if (!text) return 'Escreva o motivo: ele aparece na auditoria do cliente.'
    if (text.length < SUPPORT_REASON_MIN) return `Explique melhor (pelo menos ${SUPPORT_REASON_MIN} caracteres).`
    return null
}
