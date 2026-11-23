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

// Dados: "Saudável", "1 fonte com falha" / "2 fontes com falha" ou "Sem informação" (a API não respondeu).
export function dataOf(c: PlatformClient): Badge {
    const n = c.failingSources
    if (n === null) return { label: 'Sem informação', badge: 'badge neutral' }
    if (n === 0) return { label: 'Saudável', badge: 'badge ok' }
    return { label: n === 1 ? '1 fonte com falha' : `${n} fontes com falha`, badge: 'badge warn' }
}

// A contagem de fontes com falha vem da API (GET /sources/failing: a mesma regra da tela Unidades e fontes,
// a tentativa de leitura mais recente falhou). Organização fora da resposta = nenhuma fonte que conte.
// failing null (a API não respondeu) = sem informação: nunca a contagem antiga do Supabase, que tratava
// planilha parada há 20 min como atrasada.
export function withFailing(data: ClientsResponse, failing: Record<string, string[]> | null): ClientsResponse {
    return {
        ...data,
        clients: data.clients.map((c) => ({ ...c, failingSources: failing ? (failing[c.slug]?.length ?? 0) : null })),
    }
}

export type ClientKpis = { active: number; onboarding: number; revenue: string; failingSources: number | null }

// Os 4 indicadores do topo, calculados da lista (não ficam fixos no mock).
export function kpisOf(data: ClientsResponse): ClientKpis {
    return {
        active: data.clients.length,
        onboarding: data.clients.filter((c) => c.plan === 'onboarding').length,
        revenue: data.monthlyRevenue === null ? 'R$ [—]' : fmt.brl(data.monthlyRevenue),
        failingSources: data.clients.some((c) => c.failingSources === null)
            ? null
            : data.clients.reduce((sum, c) => sum + (c.failingSources ?? 0), 0),
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
