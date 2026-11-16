import { describe, expect, it } from 'vitest'
import { easeOutCubic, tween } from './countUp.ts'

describe('countUp', () => {
    it('começa no valor de saída e termina no de chegada', () => {
        expect(tween(0, 148, 0)).toBe(0)
        expect(tween(0, 148, 1)).toBe(148)
        expect(tween(148, 100, 1)).toBe(100) // filtro que diminui o número
    })

    it('freia no fim: na metade do tempo já passou da metade do caminho', () => {
        expect(easeOutCubic(0.5)).toBeGreaterThan(0.5)
        expect(tween(0, 100, 0.5)).toBeGreaterThan(50)
    })

    it('tempo fora de 0–1 não passa do alvo', () => {
        expect(tween(0, 10, 2)).toBe(10)
        expect(tween(0, 10, -1)).toBe(0)
    })
})
