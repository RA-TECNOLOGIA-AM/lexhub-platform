import { describe, expect, it } from 'vitest'
import { orgClosureView } from './orgClosure.ts'

const base = { slug: 'teste', name: 'Org de Teste', units: 1, members: 2, sources: 0, locked: false }

describe('impacto de encerrar organização', () => {
    it('a dona da plataforma bloqueia', () => {
        expect(orgClosureView({ ...base, locked: true }).blocked).toMatch(/dona da plataforma/)
    })
    it('lista unidades, membros e fontes', () => {
        expect(orgClosureView({ ...base, sources: 3 }).items).toEqual([
            '1 unidade some das telas',
            '2 membros perdem o acesso',
            '3 fontes são desconectadas e as senhas apagadas na hora',
        ])
    })
})
