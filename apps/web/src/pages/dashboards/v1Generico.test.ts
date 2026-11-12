import { describe, expect, it } from 'vitest'
import type { Meta } from '../../types/index.ts'
import { statsReader } from './v1Generico.ts'

const meta = { unit: 'NG' } as Meta

describe('statsReader', () => {
    it('lê os números de stats', () => {
        const n = statsReader({ meta, stats: { protocolos_resolvidos: 3, comparativo_protocolos_resolvidos: -97.12 } })
        expect(n('protocolos_resolvidos')).toBe(3)
        expect(n('comparativo_protocolos_resolvidos')).toBe(-97.12)
    })

    it('campo ausente, null ou não numérico vira null', () => {
        const n = statsReader({ meta, stats: { a: null, b: 'x', c: [1] } })
        expect(n('a')).toBeNull()
        expect(n('b')).toBeNull()
        expect(n('c')).toBeNull()
        expect(n('nao_existe')).toBeNull()
    })

    it('sem stats (mock) tudo vira null', () => {
        expect(statsReader({ meta })('protocolos_resolvidos')).toBeNull()
    })
})
