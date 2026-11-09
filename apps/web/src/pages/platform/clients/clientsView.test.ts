import { describe, expect, it } from 'vitest'
import { clients } from '../../../services/mock/clients.ts'
import type { PlatformClient } from '../../../types/index.ts'
import { billingOf, dataOf, kpisOf, planOf, validateSupportReason } from './clientsView.ts'

const [lexgroup, parceiro, escritorio] = clients.clients
const withFailing = (n: number): PlatformClient => ({ ...lexgroup, failingSources: n })

describe('selos', () => {
    it('plano, dados e cobrança de cada cliente', () => {
        expect(planOf(parceiro)).toEqual({ label: 'Implantação', badge: 'badge info' })
        expect(dataOf(lexgroup)).toEqual({ label: '1 fonte atrasada', badge: 'badge warn' })
        expect(dataOf(parceiro)).toEqual({ label: 'Saudável', badge: 'badge ok' })
        expect(billingOf(escritorio)).toEqual({ label: 'Fatura vencida', badge: 'badge danger' })
    })
    it('plural das fontes', () => {
        expect(dataOf(withFailing(2)).label).toBe('2 fontes atrasadas')
    })
})

describe('kpisOf', () => {
    it('calcula os indicadores da lista', () => {
        expect(kpisOf(clients)).toEqual({ active: 3, onboarding: 1, revenue: 'R$ [—]', failingSources: 1 })
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
