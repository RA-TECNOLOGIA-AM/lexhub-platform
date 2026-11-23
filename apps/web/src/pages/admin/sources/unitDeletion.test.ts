import { describe, expect, it } from 'vitest'
import { unitDeletionView } from './unitDeletion.ts'

const base = {
    code: 'EDT',
    name: 'Escritório de Teste',
    sources: 0,
    dashboards: 0,
    members: 0,
    locked: false,
    lastUnit: false,
}

describe('impacto de excluir unidade', () => {
    it('trava da plataforma bloqueia', () => {
        expect(unitDeletionView({ ...base, locked: true }).blocked).toMatch(/travada/)
    })
    it('última unidade bloqueia', () => {
        expect(unitDeletionView({ ...base, lastUnit: true }).blocked).toMatch(/única unidade/)
    })
    it('lista fontes, dashboards e membros no plural certo', () => {
        const v = unitDeletionView({ ...base, sources: 2, dashboards: 1, members: 3 })
        expect(v.blocked).toBeNull()
        expect(v.items[0]).toMatch(/^2 fontes deixam/)
        expect(v.items[1]).toBe('1 dashboard deixa de aparecer')
        expect(v.items[2]).toMatch(/^3 membros perdem/)
        expect(v.note).toMatch(/30 dias/)
    })
    it('unidade vazia', () => {
        expect(unitDeletionView(base).items).toEqual([
            'Nenhuma fonte ligada',
            '0 dashboards deixam de aparecer',
            'Nenhum membro ligado',
        ])
    })
})
