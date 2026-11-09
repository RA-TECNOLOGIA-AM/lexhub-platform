import type { InvoiceStatus, Plan, PlanKey } from '../../../types/index.ts'
import { fmt } from '../../../lib/format.ts'

// Módulo: as regras de texto e cor da tela de cobrança, sem React (testadas em billingView.test.ts).

// Preço de tabela: 'Sob consulta', 'R$ [PREÇO]/mês' (a definir) ou 'R$ 1.490,00/mês'.
export function priceLabel(plan: Plan): string {
    if (plan.custom) return 'Sob consulta'
    return plan.monthlyPrice === null ? 'R$ [PREÇO]/mês' : `${fmt.brl(plan.monthlyPrice)}/mês`
}

// Valor de uma fatura: 'R$ [VALOR]' (a definir) ou 'R$ 890,50'.
export const amountLabel = (amount: number | null): string => (amount === null ? 'R$ [VALOR]' : fmt.brl(amount))

// UTC nas datas: '2026-10' não pode virar setembro por causa do fuso.
const monthFmt = new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric', timeZone: 'UTC' })
const dayMonthFmt = new Intl.DateTimeFormat('pt-BR', { day: 'numeric', month: 'long', timeZone: 'UTC' })

// '2026-10' -> 'Outubro de 2026'
export function monthLabel(month: string): string {
    const text = monthFmt.format(new Date(`${month}-01T00:00:00Z`))
    return text.charAt(0).toUpperCase() + text.slice(1)
}

// '2026-12-01' -> '1 de dezembro'
export const dayMonthLabel = (date: string): string => dayMonthFmt.format(new Date(`${date}T00:00:00Z`))

// Quanto da barra pintar (0 a 100).
export function usagePct(used: number, total: number): number {
    if (total <= 0) return 0
    return Math.min(100, Math.max(0, (used / total) * 100))
}

// 'full' = chegou no limite do plano (barra âmbar, como "Histórico 24 de 24").
export const usageTone = (used: number, total: number): 'normal' | 'full' => (used >= total ? 'full' : 'normal')

// ['boleto', 'PIX'] -> 'boleto e PIX'
export function joinPt(items: string[]): string {
    if (items.length <= 1) return items.join('')
    return `${items.slice(0, -1).join(', ')} e ${items[items.length - 1]}`
}

const INVOICE_STATUS: Record<InvoiceStatus, { label: string; badge: string }> = {
    paid: { label: 'Paga', badge: 'badge ok' },
    open: { label: 'Em aberto', badge: 'badge warn' },
    overdue: { label: 'Vencida', badge: 'badge danger' },
}

export const invoiceStatusOf = (status: InvoiceStatus) => INVOICE_STATUS[status]

// Texto do botão de um plano; null = é o plano atual (mostra o selo "Seu plano").
export function planAction(plan: Plan, current: PlanKey): string | null {
    if (plan.key === current) return null
    return plan.custom ? 'Falar com vendas' : `Mudar para ${plan.name}`
}
