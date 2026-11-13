import { describe, expect, it } from 'vitest'
import { monthLabel, niceScale, parseMonth, seriesByYear, smoothPath, sortByMonth, topN } from './charts.ts'

describe('niceScale', () => {
    it('arredonda o topo do eixo como a v1', () => {
        expect(niceScale(151)).toEqual({ max: 160, ticks: [0, 40, 80, 120, 160] })
        expect(niceScale(30)).toEqual({ max: 32, ticks: [0, 8, 16, 24, 32] })
        expect(niceScale(508)).toEqual({ max: 600, ticks: [0, 150, 300, 450, 600] })
    })

    it('sem dado ainda desenha um eixo', () => {
        expect(niceScale(0)).toEqual({ max: 1, ticks: [0, 1] })
    })
})

describe('smoothPath', () => {
    it('vazio, um e dois pontos', () => {
        expect(smoothPath([])).toBe('')
        expect(smoothPath([{ x: 1, y: 2 }])).toBe('M1,2')
        expect(
            smoothPath([
                { x: 0, y: 0 },
                { x: 10, y: 5 },
            ]),
        ).toBe('M0,0L10,5')
    })

    it('três pontos: curva que começa no primeiro e termina no último', () => {
        const d = smoothPath([
            { x: 0, y: 10 },
            { x: 10, y: 0 },
            { x: 20, y: 10 },
        ])
        expect(d.startsWith('M0,10C')).toBe(true)
        expect(d.endsWith(' 20,10')).toBe(true)
    })

    it('patamar fica reto (não inventa pico)', () => {
        const d = smoothPath([
            { x: 0, y: 5 },
            { x: 10, y: 5 },
            { x: 20, y: 5 },
        ])
        expect(d).toBe('M0,5C3.33,5 6.67,5 10,5C13.33,5 16.67,5 20,5')
    })
})

describe('meses', () => {
    it('lê o formato da API e o do mock', () => {
        expect(parseMonth('nov 2026')).toEqual({ year: 2026, month: 11 })
        expect(parseMonth('2026-09')).toEqual({ year: 2026, month: 9 })
        expect(parseMonth('qualquer')).toBeNull()
        expect(monthLabel('mar 2025')).toBe('mar/2025')
    })

    it('ordena por data, não pelo texto', () => {
        const pts = [{ name: 'nov 2026' }, { name: 'abr 2026' }, { name: 'dez 2025' }]
        expect(sortByMonth(pts).map((p) => p.name)).toEqual(['dez 2025', 'abr 2026', 'nov 2026'])
    })

    it('uma linha por ano, de janeiro a dezembro', () => {
        const s = seriesByYear([
            { name: 'set 2026', value: 363 },
            { name: 'out 2026', value: 508 },
            { name: 'dez 2025', value: 10 },
        ])
        expect(s.map((y) => y.year)).toEqual([2025, 2026])
        expect(s[0].values[11]).toBe(10)
        expect(s[1].values.slice(8, 11)).toEqual([363, 508, null])
    })
})

describe('topN', () => {
    it('os maiores primeiro, empate na ordem original', () => {
        const pts = [
            { name: 'a', value: 1 },
            { name: 'b', value: 5 },
            { name: 'c', value: 1 },
        ]
        expect(topN(pts, 2).map((p) => p.name)).toEqual(['b', 'a'])
    })
})
