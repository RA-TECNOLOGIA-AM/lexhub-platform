import { describe, expect, it } from 'vitest'
import { moveKey, sortAreas, sortByOrder } from './hubOrder.ts'

const items = (...keys: string[]) => keys.map((key) => ({ key }))
const keysOf = (list: { key: string }[]) => list.map((x) => x.key)

describe('hubOrder', () => {
    it('Gestão sobe para o topo das áreas; o resto mantém a ordem do catálogo', () => {
        expect(sortAreas(['Comercial', 'Operação jurídica', 'Gestão'])).toEqual([
            'Gestão',
            'Comercial',
            'Operação jurídica',
        ])
        expect(sortAreas(['B', 'A'], [])).toEqual(['B', 'A'])
    })

    it('ordena pela lista salva', () => {
        expect(keysOf(sortByOrder(items('a', 'b', 'c'), ['c', 'a', 'b']))).toEqual(['c', 'a', 'b'])
    })

    it('dashboard fora da lista salva vai para o fim, na ordem do catálogo', () => {
        expect(keysOf(sortByOrder(items('novo1', 'a', 'novo2', 'b'), ['b', 'a']))).toEqual(['b', 'a', 'novo1', 'novo2'])
        expect(keysOf(sortByOrder(items('a', 'b'), []))).toEqual(['a', 'b'])
    })

    it('move uma key para a posição de outra (para frente e para trás)', () => {
        expect(moveKey(['a', 'b', 'c', 'd'], 'a', 'c')).toEqual(['b', 'c', 'a', 'd'])
        expect(moveKey(['a', 'b', 'c', 'd'], 'd', 'b')).toEqual(['a', 'd', 'b', 'c'])
    })

    it('move numa seção sem bagunçar a ordem relativa das outras', () => {
        // x1 e x2 são de outra seção, misturados na lista única
        const next = moveKey(['a', 'x1', 'b', 'x2', 'c'], 'a', 'c')
        expect(next.filter((k) => k.startsWith('x'))).toEqual(['x1', 'x2'])
        expect(next.filter((k) => !k.startsWith('x'))).toEqual(['b', 'c', 'a'])
    })

    it('key desconhecida ou soltar no mesmo lugar: nada muda', () => {
        const keys = ['a', 'b']
        expect(moveKey(keys, 'z', 'a')).toBe(keys)
        expect(moveKey(keys, 'a', 'a')).toBe(keys)
    })
})
