import { describe, expect, it } from 'vitest'
import { caminho, municipios, normalizar, pintar, projecao, tempoMedio, ufsDoMapa, type Municipio } from './mapa.ts'

const quadrado = (x: number, y: number): [number, number][] => [
    [x, y],
    [x + 1, y],
    [x + 1, y + 1],
    [x, y + 1],
    [x, y],
]

const geo = {
    features: [
        { properties: { id: 1, name: 'Tefé' }, geometry: { type: 'Polygon', coordinates: [quadrado(-65, -4)] } },
        {
            properties: { id: 2, name: 'Coari' },
            geometry: { type: 'MultiPolygon', coordinates: [[quadrado(-63, -4)]] },
        },
        { properties: { id: 3, name: 'Ponto' }, geometry: { type: 'Point', coordinates: [0, 0] } },
    ],
}

describe('mapa', () => {
    it('lê Polygon e MultiPolygon do GeoJSON (outros tipos ficam de fora)', () => {
        const ms = municipios(geo, 'AM')
        expect(ms.map((m) => m.name)).toEqual(['Tefé', 'Coari'])
        expect(ms[0]).toMatchObject({ id: '1', uf: 'AM' })
        expect(ms[1].aneis).toHaveLength(1)
    })

    it('a projeção cabe tudo na caixa e o caminho fecha cada anel', () => {
        const ms = municipios(geo, 'AM')
        const proj = projecao(ms, 400, 200)
        const pontos = ms.flatMap((m) => m.aneis.flat().map(proj))
        for (const [x, y] of pontos) {
            expect(x).toBeGreaterThanOrEqual(-0.01)
            expect(x).toBeLessThanOrEqual(400.01)
            expect(y).toBeGreaterThanOrEqual(-0.01)
            expect(y).toBeLessThanOrEqual(200.01)
        }
        expect(caminho(ms[0], proj)).toMatch(/^M[\d.]+,[\d.]+(L[\d.]+,[\d.]+)+Z$/)
    })

    it('casa município e comarca pelo nome sem acento, na mesma UF', () => {
        const ms: Municipio[] = [
            ...municipios(geo, 'AM'),
            { id: '9', name: 'Lugar Nenhum', uf: 'AM', aneis: [quadrado(-60, -3)] },
        ]
        const pintados = pintar(
            ms,
            [
                { name: 'TEFE', value: 16, uf: 'AM', tempoMedio: 301.2 },
                { name: 'TEFE', value: 99, uf: 'PA', tempoMedio: 1 }, // outra UF: não conta
            ],
            [{ name: 'TEFE', value: 5000, uf: 'AM' }],
            ['TEFE', 'COARI'],
        )
        const [tefe, coari, nenhum] = pintados
        expect(tefe).toMatchObject({
            comarca: 'TEFE',
            categoria: 'colorido',
            quantidade: 16,
            valor: 5000,
            tempoMedio: 301.2,
            intensidade: 1,
        })
        expect(coari).toMatchObject({ comarca: 'COARI', categoria: 'zero', quantidade: 0, intensidade: 0 })
        expect(nenhum).toMatchObject({ comarca: null, categoria: 'fora_base' })
    })

    it('mostra só as UFs com dados e com contorno', () => {
        const p = (uf: string) => ({ name: 'X', value: 1, uf, tempoMedio: null })
        expect(ufsDoMapa([p('pa'), p('AM'), p('SP'), p(''), p('AM')])).toEqual(['AM', 'PA'])
    })

    it('normaliza nomes e formata o tempo médio como a v1', () => {
        expect(normalizar(' São Gabriel da Cachoeira ')).toBe('SAO GABRIEL DA CACHOEIRA')
        expect(tempoMedio(null)).toBe('—')
        expect(tempoMedio(0.5)).toBe('12h')
        expect(tempoMedio(214.6)).toBe('214d 14h')
        expect(tempoMedio(3)).toBe('3d')
    })
})
