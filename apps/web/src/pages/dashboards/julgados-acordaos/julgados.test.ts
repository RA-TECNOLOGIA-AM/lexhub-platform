import { describe, expect, it } from 'vitest'
import { lerJulgadosAcordaos } from './fields.ts'
import {
    acordaosPorAno,
    CAPITAL_POR_UF,
    GEO_POR_UF,
    avisosDadosFaltando,
    composicao,
    contarPorCampo,
    coresDosAnos,
    dataBr,
    mapaDaUnidade,
    numeroCnj,
    ordenarLista,
    taxaDoAno,
    totalDoAno,
} from './julgados.ts'
import type { LinhaAcordao, PontoJulgados } from './types.ts'
import { normalizarComarca } from '../../../lib/comarcaMapa.ts'
import { julgadosAcordaosFor } from '../../../services/mock/julgadosAcordaos.ts'
import ac from '../../../../public/geo/ac-municipios.json?raw'
import am from '../../../../public/geo/amazonas-municipios.json?raw'
import ba from '../../../../public/geo/ba-municipios.json?raw'
import ma from '../../../../public/geo/ma-municipios.json?raw'
import pa from '../../../../public/geo/pa-municipios.json?raw'
import pb from '../../../../public/geo/pb-municipios.json?raw'
import rj from '../../../../public/geo/rj-municipios.json?raw'

const vazio = lerJulgadosAcordaos({
    meta: { unit: 'NG', from: '', to: '', source: '', synced_at: null, timezone: '' },
    stats: {},
}).n

const ponto = (name: string, value: number, extra: Partial<PontoJulgados> = {}): PontoJulgados => ({
    name,
    value,
    valorCausa: null,
    uf: null,
    tempoMedioDias: null,
    ...extra,
})

describe('composicao (card Taxa de procedência)', () => {
    it('procedentes ÷ decididos; não classificados fora da conta', () => {
        const c = composicao({ ...vazio, total: 50, procedentes: 20, improcedentes: 15, extintos: 5 })
        expect(c.decididos).toBe(40)
        expect(c.naoClassificados).toBe(10)
        expect(c.taxa).toBe(50)
        expect(c.pct).toEqual({ procedente: 50, improcedente: 37.5, extinto: 12.5 })
        expect(c.temDados).toBe(true)
    })

    it('sem acórdão decidido: sem dados e tudo 0', () => {
        const c = composicao({ ...vazio, total: 3 })
        expect(c.temDados).toBe(false)
        expect(c.taxa).toBe(0)
        expect(c.naoClassificados).toBe(3)
    })
})

describe('histórico por ano (gráficos mês a mês)', () => {
    const porMes = {
        procedentes: [ponto('mar 2023', 99), ponto('jan 2025', 4), ponto('out 2026', 6), ponto('2026-11', 2)],
        improcedentes: [ponto('jan 2025', 1), ponto('out 2026', 3)],
        extintos: [ponto('out 2026', 1)],
    }
    const anos = acordaosPorAno(porMes)

    it('um ano por linha desde 2024, meses sem acórdão valem 0 (v1)', () => {
        expect(anos.map((a) => a.ano)).toEqual([2025, 2026])
        expect(anos[0].procedente[0]).toBe(4)
        expect(anos[0].procedente[1]).toBe(0)
        expect(anos[1].procedente[9]).toBe(6)
        expect(anos[1].procedente[10]).toBe(2) // 'AAAA-MM' do mock também vale
        expect(anos[1].extinto).toHaveLength(12)
    })

    it('total do mês e taxa da categoria (uma casa; mês sem decidido fica sem ponto)', () => {
        expect(totalDoAno(anos[1])[9]).toBe(10)
        expect(taxaDoAno(anos[1], 'procedente')[9]).toBe(60)
        expect(taxaDoAno(anos[1], 'improcedente')[9]).toBe(30)
        expect(taxaDoAno(anos[1], 'extinto')[0]).toBeNull()
        expect(taxaDoAno(anos[0], 'improcedente')[0]).toBe(20)
    })

    it('cores: ano atual laranja e contínuo; os outros ciclam a paleta, tracejados', () => {
        expect(coresDosAnos([2024, 2025, 2026], 2026)).toEqual([
            { color: '#6366f1', dashed: true },
            { color: '#14b8a6', dashed: true },
            { color: '#f97316', dashed: false },
        ])
    })
})

describe('faixa "Atenção"', () => {
    it('as mensagens da v1, na ordem da v1, só as que têm processo', () => {
        const avisos = avisosDadosFaltando({ ...vazio, semRelator: 3, meritoSemData: 1, semValorPe: 1200, semUf: 0 })
        expect(avisos).toEqual([
            'Existem 1 processo(s) com mérito do acórdão lançado e sem a data do acórdão — não entram em nenhuma contagem!',
            'Existem 3 processo(s) com acórdão sem o nome do relator!',
            'Existem 1.200 processo(s) com acórdão procedente com proveito econômico sem o valor do acórdão!',
        ])
        expect(avisosDadosFaltando(vazio)).toEqual([])
    })

    it('conta por informação faltando, da mais comum à menos', () => {
        expect(contarPorCampo([{ campo: 'UF' }, { campo: 'Relator' }, { campo: 'Relator' }])).toEqual([
            ['Relator', 2],
            ['UF', 1],
        ])
    })
})

describe('lista "Acórdãos no período"', () => {
    const linha = (numero: string, data: string | null, relator = 'Ana'): LinhaAcordao => ({
        id: null,
        numero_processo: numero,
        fase: 'Recursal',
        subfase: 'Arquivado',
        status_2g: 'Procedente',
        uf: 'AM',
        relator,
        data_acordao: data,
        status_acordao_embargos: '',
        data_acordao_embargos: null,
    })
    const itens = [
        linha('06000001020248040012', '2026-10-02'),
        linha('1', null),
        linha('2', '2026-10-20', 'José Araújo'),
    ]

    it('ordena pela data do acórdão; sem data vai para o fim', () => {
        expect(ordenarLista(itens, 'data_recente').map((r) => r.numero_processo)).toEqual([
            '2',
            '06000001020248040012',
            '1',
        ])
        expect(ordenarLista(itens, 'data_antiga').map((r) => r.numero_processo)).toEqual([
            '06000001020248040012',
            '2',
            '1',
        ])
    })

    it('formatos (CNJ e data)', () => {
        expect(numeroCnj('06000001020248040012')).toBe('0600000-10.2024.8.04.0012')
        expect(numeroCnj('123')).toBe('123')
        expect(dataBr('2026-10-05')).toBe('05/10/2026')
        expect(dataBr(null)).toBe('—')
    })
})

describe('mapa das improcedências por comarca', () => {
    // Os nomes dos municípios de cada GeoJSON servido em public/geo/ (os mesmos arquivos da v1).
    const municipios = Object.fromEntries(
        Object.entries({ AC: ac, AM: am, BA: ba, MA: ma, PA: pa, PB: pb, RJ: rj }).map(([uf, texto]) => [
            uf,
            new Set(
                (JSON.parse(texto) as { features: { properties: { name: string } }[] }).features.map((f) =>
                    normalizarComarca(f.properties.name),
                ),
            ),
        ]),
    )

    it('NG mostra os estados da base com a capital de cada um; LA e RJ, o mapa do próprio estado', () => {
        expect(Object.keys(GEO_POR_UF).sort()).toEqual(Object.keys(CAPITAL_POR_UF).sort())
        expect(mapaDaUnidade('NG').geo).toEqual({ porUf: GEO_POR_UF })
        expect(mapaDaUnidade('LA')).toEqual({ geo: { url: '/geo/amazonas-municipios.json' }, capital: 'Manaus' })
        expect(mapaDaUnidade('RJ')).toEqual({ geo: { url: '/geo/rj-municipios.json' }, capital: 'Rio de Janeiro' })
        for (const [uf, capital] of Object.entries(CAPITAL_POR_UF)) {
            expect(municipios[uf].has(normalizarComarca(capital))).toBe(true)
        }
    })

    it('no mock, toda comarca existe no mapa (senão o modo mock não pinta nada)', () => {
        const q = { org: 'lexgroup', unit: '', from: '2024-01-01', to: '2026-11-16' }
        for (const [unit, suf, ufFixa] of [
            ['NG', 'NG', null],
            ['LA_AM', 'LA', 'AM'],
            ['LA_RJ', 'RJ', 'RJ'],
        ] as const) {
            const r = julgadosAcordaosFor(unit, { ...q, unit })
            const comarcas = r.stats?.[`julgados_comarca_opcoes_${suf}`] as string[]
            const porComarca = r[`julgados_acordao_improcedencia_por_comarca_estoque_${suf}`] as {
                name: string
                uf: string | null
            }[]
            expect(porComarca.length).toBeGreaterThan(0)
            for (const p of porComarca.filter((x) => x.name !== 'Sem comarca' && (ufFixa || x.uf))) {
                expect(municipios[ufFixa ?? (p.uf as string)].has(normalizarComarca(p.name))).toBe(true)
            }
            for (const c of comarcas) {
                expect(Object.values(municipios).some((s) => s.has(normalizarComarca(c)))).toBe(true)
            }
        }
    })
})
