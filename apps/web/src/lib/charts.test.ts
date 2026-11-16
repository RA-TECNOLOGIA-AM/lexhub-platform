import { describe, expect, it } from 'vitest'
import {
    monthLabel,
    niceScale,
    parseMonth,
    seriesByYear,
    smoothPath,
    sortByMonth,
    spreadLabels,
    pieSlices,
    arcPath,
    spreadColumn,
    topN,
} from './charts.ts'

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

describe('spreadLabels', () => {
    it('mantém no meio da parte os rótulos que não encostam', () => {
        expect(spreadLabels([300, 250, 200])).toEqual([300, 250, 200])
    })
    it('empurra para cima o rótulo que encosta no de baixo', () => {
        expect(spreadLabels([300, 296, 293])).toEqual([300, 287, 274])
    })
    it('lista vazia', () => {
        expect(spreadLabels([])).toEqual([])
    })
})

describe('pieSlices', () => {
    const items = [
        { name: 'A', value: 50 },
        { name: 'B', value: 30 },
        { name: 'C', value: 0 },
        { name: 'D', value: 10 },
        { name: 'E', value: 10 },
    ]
    it('ordena do maior ao menor, sem fatias zeradas, e fecha a volta', () => {
        const s = pieSlices(items)
        expect(s.map((p) => p.name)).toEqual(['A', 'B', 'D', 'E'])
        expect(s[0]).toMatchObject({ start: 0, end: 0.5, share: 50, others: 0 })
        expect(s[s.length - 1].end).toBe(1)
    })
    it('junta o que passa do limite em "Outras"', () => {
        const s = pieSlices(items, 2)
        expect(s.map((p) => [p.name, p.value, p.others])).toEqual([
            ['A', 50, 0],
            ['B', 30, 0],
            ['Outras', 20, 2],
        ])
    })
    it('não cria "Outras" com uma rubrica só', () => {
        expect(pieSlices(items, 3).map((p) => p.name)).toEqual(['A', 'B', 'D', 'E'])
    })
    it('sort = false mantém a ordem recebida', () => {
        expect(pieSlices(items, 10, 'Outras', false).map((p) => p.name)).toEqual(['A', 'B', 'D', 'E'])
        const inv = [...items].reverse()
        expect(pieSlices(inv, 10, 'Outras', false).map((p) => p.name)).toEqual(['E', 'D', 'B', 'A'])
    })
    it('sem valores, sem fatias', () => {
        expect(pieSlices([{ name: 'A', value: 0 }])).toEqual([])
    })
})

describe('arcPath', () => {
    it('meia volta a partir do topo', () => {
        expect(arcPath(100, 100, 50, 0, 0.5)).toBe('M100,100L100.00,50.00A50,50 0 0 1 100.00,150.00Z')
    })
    it('fatia de rosca: arco de fora, desce ao anel de dentro e volta', () => {
        expect(arcPath(100, 100, 50, 0, 0.25, 30)).toBe(
            'M100.00,50.00A50,50 0 0 1 150.00,100.00L130.00,100.00A30,30 0 0 0 100.00,70.00Z',
        )
    })
})

describe('spreadColumn', () => {
    it('não mexe em quem já está longe', () => {
        expect(spreadColumn([10, 50, 90], 15, 0, 100)).toEqual([10, 50, 90])
    })
    it('afasta os que se encostam, mantendo a ordem da entrada', () => {
        expect(spreadColumn([52, 50, 51], 15, 0, 200)).toEqual([80, 50, 65])
    })
    it('respeita os limites de cima e de baixo', () => {
        expect(spreadColumn([95, 96, 97], 10, 0, 100)).toEqual([80, 90, 100])
        expect(spreadColumn([-5, 0], 10, 0, 100)).toEqual([0, 10])
    })
})
