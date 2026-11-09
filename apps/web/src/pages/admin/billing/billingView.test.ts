import { describe, expect, it } from 'vitest'
import type { Plan } from '../../../types/index.ts'
import {
    amountLabel,
    dayMonthLabel,
    invoiceStatusOf,
    joinPt,
    monthLabel,
    planAction,
    priceLabel,
    usagePct,
    usageTone,
} from './billingView.ts'

const plan = (over: Partial<Plan>): Plan => ({
    key: 'starter',
    name: 'Starter',
    monthlyPrice: null,
    custom: false,
    tagline: '',
    features: [],
    ...over,
})

// Intl usa espaço não separável depois do "R$"; normaliza para comparar.
const plain = (s: string) => s.replace(/\s/g, ' ')

describe('preço e valor', () => {
    it('preço ainda não definido vira [PREÇO]', () => {
        expect(priceLabel(plan({}))).toBe('R$ [PREÇO]/mês')
    })
    it('preço definido sai em reais', () => {
        expect(plain(priceLabel(plan({ monthlyPrice: 1490 })))).toBe('R$ 1.490,00/mês')
    })
    it('plano sob consulta ignora o preço', () => {
        expect(priceLabel(plan({ custom: true, monthlyPrice: 10 }))).toBe('Sob consulta')
    })
    it('valor de fatura', () => {
        expect(amountLabel(null)).toBe('R$ [VALOR]')
        expect(plain(amountLabel(890.5))).toBe('R$ 890,50')
    })
})

describe('datas', () => {
    it('mês por extenso com inicial maiúscula', () => {
        expect(monthLabel('2026-10')).toBe('Outubro de 2026')
        expect(monthLabel('2026-01')).toBe('Janeiro de 2026')
    })
    it('dia e mês da renovação', () => {
        expect(dayMonthLabel('2026-12-01')).toBe('1 de dezembro')
    })
})

describe('uso do plano', () => {
    it('porcentagem fica entre 0 e 100', () => {
        expect(usagePct(42, 60)).toBe(70)
        expect(usagePct(70, 60)).toBe(100)
        expect(usagePct(3, 0)).toBe(0)
    })
    it('só muda de tom quando chega no limite', () => {
        expect(usageTone(12, 15)).toBe('normal')
        expect(usageTone(24, 24)).toBe('full')
        expect(usageTone(61, 60)).toBe('full')
    })
})

describe('textos', () => {
    it('junta lista com "e"', () => {
        expect(joinPt(['boleto'])).toBe('boleto')
        expect(joinPt(['boleto', 'PIX'])).toBe('boleto e PIX')
        expect(joinPt(['boleto', 'PIX', 'cartão'])).toBe('boleto, PIX e cartão')
    })
    it('situação da fatura', () => {
        expect(invoiceStatusOf('paid')).toEqual({ label: 'Paga', badge: 'badge ok' })
        expect(invoiceStatusOf('overdue').badge).toBe('badge danger')
    })
    it('ação de cada plano', () => {
        expect(planAction(plan({ key: 'pro' }), 'pro')).toBeNull()
        expect(planAction(plan({}), 'pro')).toBe('Mudar para Starter')
        expect(planAction(plan({ key: 'enterprise', custom: true }), 'pro')).toBe('Falar com vendas')
    })
})
