import { describe, expect, it } from 'vitest'
import { clients } from '../../../services/mock/clients.ts'
import type { PlatformClient } from '../../../types/index.ts'
import { billingOf, dataOf, kpisOf, planOf, validateSupportReason, withFailing } from './clientsView.ts'

const [lexgroup, parceiro, escritorio] = clients.clients
const failing = (n: number | null): PlatformClient => ({ ...lexgroup, failingSources: n })

describe('selos', () => {
    it('plano, dados e cobrança de cada cliente', () => {
        expect(planOf(parceiro)).toEqual({ label: 'Implantação', badge: 'badge info' })
        expect(dataOf(lexgroup)).toEqual({ label: '1 fonte com falha', badge: 'badge warn' })
        expect(dataOf(parceiro)).toEqual({ label: 'Saudável', badge: 'badge ok' })
        expect(billingOf(escritorio)).toEqual({ label: 'Fatura vencida', badge: 'badge danger' })
    })
    it('plural das fontes', () => {
        expect(dataOf(failing(2)).label).toBe('2 fontes com falha')
    })
    it('sem a contagem da API: "Sem informação", nunca um número da regra antiga', () => {
        expect(dataOf(failing(null))).toEqual({ label: 'Sem informação', badge: 'badge neutral' })
    })
})

describe('withFailing (contagem da API, a mesma regra da tela Unidades e fontes)', () => {
    it('troca a contagem do Supabase pela da API; organização fora da resposta = 0', () => {
        const out = withFailing(clients, { lexgroup: ['sheets_financeiro_la'] })
        expect(out.clients.map((c) => [c.slug, c.failingSources])).toEqual([
            ['lexgroup', 1],
            [parceiro.slug, 0],
            [escritorio.slug, 0],
        ])
    })
    it('a API não respondeu: todas sem informação (a regra antiga contava planilha parada como atrasada)', () => {
        expect(withFailing(clients, null).clients.every((c) => c.failingSources === null)).toBe(true)
    })
})

describe('kpisOf', () => {
    it('calcula os indicadores da lista', () => {
        expect(kpisOf(clients)).toEqual({ active: 3, onboarding: 1, revenue: 'R$ [—]', failingSources: 1 })
    })
    it('sem a contagem da API: indicador vazio', () => {
        expect(kpisOf(withFailing(clients, null)).failingSources).toBeNull()
    })
    it('receita definida sai em reais', () => {
        expect(kpisOf({ ...clients, monthlyRevenue: 12000 }).revenue.replace(/\s/g, ' ')).toBe('R$ 12.000,00')
    })
})

describe('validateSupportReason', () => {
    it('motivo vazio ou curto não passa', () => {
        expect(validateSupportReason('   ')).toBe('Escreva o motivo: ele aparece na auditoria do cliente.')
        expect(validateSupportReason('ver erro')).toBe('Explique melhor (pelo menos 10 caracteres).')
    })
    it('motivo com conteúdo passa', () => {
        expect(validateSupportReason('Conferir divergência no Protocolo, chamado #42')).toBeNull()
    })
})
