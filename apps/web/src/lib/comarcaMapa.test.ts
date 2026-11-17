import { describe, expect, it } from 'vitest'
import {
    aCadaDez,
    capitalInterior,
    normalizarComarca,
    resolverMunicipios,
    resumoMapa,
    revertidos,
    semComarca,
    tempoMedio,
    ufsComDados,
    type Municipio,
} from './comarcaMapa.ts'

const AM: Municipio[] = [
    { uf: 'AM', id: '1', nome: 'Manaus' },
    { uf: 'AM', id: '2', nome: 'Tefé' },
    { uf: 'AM', id: '3', nome: 'Parintins' },
    { uf: 'AM', id: '4', nome: 'Japurá' }, // sem comarca na base
]
const PA: Municipio[] = [{ uf: 'PA', id: '5', nome: 'Belém' }]

describe('casamento município × comarca', () => {
    it('nome sem acento e maiúsculo', () => {
        expect(normalizarComarca(' São Gonçalo ')).toBe('SAO GONCALO')
        expect(normalizarComarca('Tefé')).toBe(normalizarComarca('TEFE'))
    })

    it('vários estados: UF + nome; categorias e intensidade pela raiz quadrada', () => {
        const m = resolverMunicipios(
            [...AM, ...PA],
            {
                quantidade: [
                    { name: 'MANAUS', value: 16, uf: 'AM', tempoMedioDias: 200.5 },
                    { name: 'Tefe', value: 4, uf: 'AM' },
                    { name: 'Belém', value: 1, uf: 'AM' }, // UF errada: não pinta Belém do PA
                ],
                valor: [{ name: 'Manaus', value: 5000, uf: 'AM' }],
                comarcas: ['Manaus', 'Tefé', 'Parintins', 'Belém'],
                selecionadas: ['tefé'],
            },
            true,
        )
        const por = Object.fromEntries(m.map((x) => [x.nome, x]))
        expect(por.Manaus).toMatchObject({ categoria: 'colorido', quantidade: 16, valor: 5000, intensidade: 1 })
        expect(por.Manaus.comarca).toBe('Manaus')
        expect(por.Manaus.tempoMedioDias).toBe(200.5)
        expect(por['Tefé']).toMatchObject({ categoria: 'colorido', intensidade: 0.5, ativo: true })
        expect(por.Parintins.categoria).toBe('zero')
        expect(por['Japurá']).toMatchObject({ categoria: 'fora_base', comarca: null })
        expect(por['Belém'].categoria).toBe('zero')
        expect(resumoMapa(m)).toEqual({ coloridos: 2, zeros: 2, foraBase: 1, totalProcessos: 20, maximo: 16 })
    })

    it('um estado: só o nome (a UF não importa)', () => {
        const m = resolverMunicipios(
            AM,
            {
                quantidade: [{ name: 'Manaus', value: 9 }],
                valor: [],
                comarcas: ['Manaus'],
                selecionadas: [],
            },
            false,
        )
        expect(m.find((x) => x.nome === 'Manaus')).toMatchObject({ categoria: 'colorido', intensidade: 1 })
        expect(m.filter((x) => x.categoria === 'fora_base')).toHaveLength(3)
    })

    it('UFs mostradas: as que têm dado e mapa, em ordem', () => {
        const urls = { AM: '/geo/amazonas-municipios.json', PA: '/geo/pa-municipios.json' }
        expect(
            ufsComDados(
                [
                    { name: 'X', value: 1, uf: 'pa' },
                    { name: 'Y', value: 1, uf: 'AM' },
                    { name: 'Z', value: 1, uf: 'SP' },
                    { name: 'W', value: 1 },
                ],
                urls,
            ),
        ).toEqual(['AM', 'PA'])
    })
})

describe('legenda do mapa (as contas da v1)', () => {
    const q = [
        { name: 'Manaus', value: 6, uf: 'AM' },
        { name: 'Belém', value: 2, uf: 'PA' },
        { name: 'Parintins', value: 2, uf: 'AM' },
        { name: 'Sem comarca', value: 5 },
    ]

    it('Capital × Interior: capital de cada UF ou do estado; "Sem comarca" fora', () => {
        expect(capitalInterior(q, { AM: 'Manaus', PA: 'Belém' })).toEqual({
            capital: 8,
            interior: 2,
            capitalPct: 80,
            interiorPct: 20,
        })
        expect(capitalInterior(q, 'Manaus')?.capital).toBe(6)
        expect(capitalInterior([{ name: 'Sem comarca', value: 3 }], 'Manaus')).toBeNull()
    })

    it('"a cada 10" e a 3ª coluna usam a soma pintada no mapa', () => {
        expect(aCadaDez(25, 100)).toBe(2.5)
        expect(aCadaDez(0, 100)).toBeNull()
        expect(aCadaDez(25, 0)).toBeNull()
        expect(revertidos(5, 20)).toEqual({ revertidas: 5, pct: 25 })
        expect(revertidos(undefined, 20)).toBeNull()
        expect(revertidos(3, 0)).toBeNull()
    })

    it('processos sem comarca e o tempo médio da dica', () => {
        expect(semComarca(q, [{ name: 'SEM COMARCA', value: 900 }])).toEqual({ quantidade: 5, valor: 900 })
        expect(tempoMedio(null)).toBe('—')
        expect(tempoMedio(0.5)).toBe('12h')
        expect(tempoMedio(3)).toBe('3d')
        expect(tempoMedio(3.25)).toBe('3d 6h')
    })
})
