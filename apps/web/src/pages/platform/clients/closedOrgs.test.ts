import { describe, expect, it } from 'vitest'
import { closedSub } from './clientsView.ts'

describe('organização encerrada', () => {
    const now = new Date('2026-11-24T12:00:00Z').getTime()
    const base = { slug: 'teste', name: 'Teste', closedAt: '2026-11-24T10:00:00Z', purgeAt: '2026-12-24T10:00:00Z' }
    it('dias até apagar de vez e quem encerrou', () => {
        expect(closedSub({ ...base, closedBy: 'ana@lexgroup.com.br' }, now)).toBe(
            'Apagada de vez em 30 dias · por ana@lexgroup.com.br',
        )
        expect(closedSub({ ...base, closedBy: null, purgeAt: '2026-11-25T10:00:00Z' }, now)).toBe(
            'Apagada de vez amanhã',
        )
    })
})
