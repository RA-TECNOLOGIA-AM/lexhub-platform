import { describe, expect, it } from 'vitest'
import { contagemAbas, daAba } from './rubricas.ts'

const demandas = [
    { id: 1, situacao: 'represado' as const, protocolado: false },
    { id: 2, situacao: 'resolvido' as const, protocolado: true },
    { id: 3, situacao: 'resolvido' as const, protocolado: false },
]

describe('abas do modal de rubricas', () => {
    it('conta cada aba (protocolado pode ser também resolvido)', () => {
        expect(contagemAbas(demandas)).toEqual({ todos: 3, resolvidos: 2, represados: 1, protocolados: 1 })
    })

    it('filtra as demandas da aba', () => {
        expect(daAba(demandas, 'represados').map((d) => d.id)).toEqual([1])
        expect(daAba(demandas, 'protocolados').map((d) => d.id)).toEqual([2])
        expect(daAba(demandas, 'todos')).toHaveLength(3)
    })
})
