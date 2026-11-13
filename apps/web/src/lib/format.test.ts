import { describe, expect, it } from 'vitest'
import { duracao, fmt } from './format.ts'

describe('duracao', () => {
    it('minutos, horas e dias como na v1', () => {
        expect(duracao(0)).toBe('0min')
        expect(duracao(58 / 1440)).toBe('58min')
        expect(duracao((8 * 60 + 10) / 1440)).toBe('8h 10min')
        expect(duracao(0.5)).toBe('12h')
        expect(duracao(2 + 3 / 24)).toBe('2d 3h')
        expect(duracao(3)).toBe('3d')
    })
})

describe('pct2', () => {
    it('duas casas, vírgula decimal', () => {
        expect(fmt.pct2(46.534)).toBe('46,53%')
        expect(fmt.pct2(0)).toBe('0,00%')
    })
})
