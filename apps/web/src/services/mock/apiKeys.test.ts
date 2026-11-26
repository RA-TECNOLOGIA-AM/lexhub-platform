import { describe, expect, it } from 'vitest'
import { createMockApiKeys } from './apiKeys.ts'
import { DataError } from '../errors.ts'

const NOW = Date.parse('2026-11-26T12:00:00Z')
const ANA = { name: 'Ana', email: 'ana@x.com' }
const extra = (validade = '2027-01-31', justificativa = 'Automação de metas') => ({
    setor: 'Protocolo',
    justificativa,
    validade,
})

describe('createMockApiKeys', () => {
    it('pede, aprova só os extras marcados e gera tokens', () => {
        const store = createMockApiKeys(() => NOW)
        const id = store.request(ANA, 'Power BI', [extra(), { ...extra(), setor: 'Financeiro' }])
        expect(() => store.tokens(ANA)).toThrow(DataError)
        expect(store.count()).toBe(2)
        const key = store.decide(id, true, ['Protocolo'], null)
        expect(key.status).toBe('active')
        expect(key.sectors.map((s) => [s.setor, s.status])).toEqual([
            ['Comercial', 'approved'],
            ['Protocolo', 'approved'],
            ['Financeiro', 'rejected'],
        ])
        expect(store.tokens(ANA).refreshToken).toMatch(/^lxr_/)
    })

    it('valida justificativa, validade e pedido repetido', () => {
        const store = createMockApiKeys(() => NOW)
        expect(() => store.request(ANA, null, [extra('2027-01-31', 'curta')])).toThrow('10 caracteres')
        expect(() => store.request(ANA, null, [extra('2027-11-27')])).toThrow('365 dias')
        expect(() => store.request(ANA, null, [extra('2026-11-26')])).toThrow('365 dias')
        expect(() => store.request(ANA, null, [{ ...extra(), setor: 'Comercial' }])).toThrow('já é um setor seu')
        store.request(ANA, null, [])
        expect(() => store.request(ANA, null, [])).toThrow('já tem uma chave')
    })

    it('revoga setor sem derrubar a chave, depois revoga a chave', () => {
        const store = createMockApiKeys(() => NOW)
        const id = store.request(ANA, null, [extra()])
        store.decide(id, true, ['Protocolo'], null)
        store.revokeSector(id, 'Protocolo')
        expect(store.mine(ANA)?.status).toBe('active')
        expect(store.mine(ANA)?.sectors.find((s) => s.setor === 'Protocolo')?.status).toBe('revoked')
        store.revoke(id)
        expect(store.list('closed').map((k) => k.id)).toContain(id)
        expect(() => store.revoke(id)).toThrow('encerrada')
    })
})
