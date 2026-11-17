import { describe, expect, it } from 'vitest'
import {
    alvarasPorDia,
    atividadesConfeccao,
    alvarasPorMes,
    comparativo,
    diasUteisAte,
    distribuicoes,
    escopoDe,
    indicadores,
    lados,
    mediaEMediana,
    mesAno,
    porAno,
    previsaoCompensacao,
    series,
    somaComarcas,
    somaPorNome,
    type EstrategicoResponse,
} from './estrategico.ts'
import { estrategicoFilters } from './filters.ts'
import { execucaoEstrategicoFor } from '../../../services/mock/execucaoEstrategico.ts'

const meta = {
    unit: 'NG',
    from: '',
    to: '',
    source: 'LexFlow',
    generated_at: '',
} as unknown as EstrategicoResponse['meta']
const resp = (): EstrategicoResponse => ({
    meta,
    condenacao: {
        atual: {
            stats: {
                total_em_execucao: 10,
                total_saida_execucao_periodo: 4,
                valor_em_execucao: 1000,
                duracoes_tempo_execucao_NG: [10, 30],
                valor_ted_saida_execucao_periodo: 50,
                estoque_inicial: 100,
            },
        },
        historico: {
            stats: { total_em_execucao: 200, valor_total_em_execucao: 20_000, valor_remanescente_em_execucao: 7 },
            quantidade_entrada_execucao_por_mes: [{ name: 'jan 2026', value: 3 }],
            valor_entrada_execucao_por_mes: [{ name: 'jan 2026', value: 300 }],
            execucao_por_comarca_total: [{ name: 'MANAUS', value: 2, valor_execucao: 10, tempo_medio_dias: 100 }],
        },
        anterior: { stats: { total_em_execucao: 5, total_saida_execucao_periodo: 4 } },
    },
    acordos: {
        atual: {
            stats: {
                total_entrada_execucao_acordos_periodo_NG: 2,
                valor_entrada_execucao_acordos_periodo_NG: 200,
                duracoes_tempo_execucao_acordos_NG: [20],
                valor_ted_saida_execucao_acordos_periodo_NG: 5,
                estoque_inicial_execucao_acordos_NG: 50,
            },
        },
        historico: {
            stats: { total_em_execucao_acordos_NG: 100, valor_total_em_execucao_acordos_NG: 5_000 },
            quantidade_entrada_execucao_acordos_por_mes_NG: [{ name: 'jan 2026', value: 1 }],
            valor_entrada_execucao_acordos_por_mes_NG: [{ name: 'jan 2026', value: 100 }],
            execucao_acordos_por_comarca_total_NG: [
                { name: 'MANAUS', value: 2, valor_execucao: 5, tempo_medio_dias: 50 },
            ],
        },
        anterior: { stats: {} },
    },
})

describe('helpers da v1', () => {
    it('escopo: só condenacao/acordos, senão ambos', () => {
        expect(escopoDe(undefined)).toBe('ambos')
        expect(escopoDe(['acordos'])).toBe('acordos')
        expect(escopoDe(['x'])).toBe('ambos')
    })
    it('soma por nome, do maior para o menor', () => {
        expect(
            somaPorNome(
                [{ name: 'a', value: 1 }],
                [
                    { name: 'b', value: 3 },
                    { name: 'a', value: 1 },
                ],
            ),
        ).toEqual([
            { name: 'b', value: 3 },
            { name: 'a', value: 2 },
        ])
    })
    it('comarcas: tempo médio ponderado pela quantidade', () => {
        const [m] = somaComarcas(
            [{ name: 'M', value: 1, valor_execucao: 1, tempo_medio_dias: 10 }],
            [{ name: 'M', value: 3, valor_execucao: 2, tempo_medio_dias: 30 }],
        )
        expect(m).toEqual({ name: 'M', value: 4, valor: 3, tempoMedio: 25 })
    })
    it('média e mediana; comparativo com anterior 0 = 0', () => {
        expect(mediaEMediana([3, 1, 2, 10])).toEqual({ media: 4, mediana: 2.5 })
        expect(mediaEMediana([])).toEqual({ media: 0, mediana: 0 })
        expect(comparativo(15, 10)).toBe(50)
        expect(comparativo(5, 0)).toBe(0)
    })
    it('mês abreviado e séries por ano', () => {
        expect(mesAno('mar 2025')).toEqual({ ano: '2025', mes: 2 })
        expect(mesAno('2025-03')).toBeNull()
        expect(
            porAno([{ name: 'fev 2026', value: 4 }])
                .get('2026')
                ?.slice(0, 3),
        ).toEqual([null, 4, null])
    })
})

describe('a página', () => {
    it('indicadores somam os dois lados (durações juntas, TED somado)', () => {
        const k = indicadores(lados(resp(), 'ambos'))
        expect(k.total).toBe(300)
        expect(k.valorTotal).toBe(25_000)
        expect(k.entradas).toBe(12)
        expect(k.compEntradas).toBe(140)
        expect(k.valorEntrada).toBe(1200)
        expect(k.mediaTempo).toBe(20)
        expect(k.medianaTempo).toBe(20)
        expect(k.valorTed).toBe(55)
        expect(k.estoqueInicial).toBe(150)
        expect(k.valorRemanescente).toBe(7)
    })
    it('o escopo tira o outro lado', () => {
        expect(indicadores(lados(resp(), 'acordos')).total).toBe(100)
        expect(indicadores(lados(resp(), 'condenacao')).entradas).toBe(10)
        expect(indicadores(lados(resp(), 'acordos')).valorRemanescente).toBe(0)
    })
    it('séries e ticket somam antes de dividir', () => {
        const s = series(lados(resp(), 'ambos'))
        expect(s.anos).toEqual(['2026'])
        expect(s.qtdEntradaAno.get('2026')?.[0]).toBe(4)
        expect(s.ticketAno.get('2026')?.[0]).toBe(100)
    })
    it('comarcas com o tempo fixo da v1 (primeiro encontrado)', () => {
        const d = distribuicoes(lados(resp(), 'ambos'))
        expect(d.comarca.total).toEqual([{ name: 'MANAUS', value: 4, valor: 15, tempoMedio: 100 }])
        expect(d.condenacaoAcordos.total).toEqual([
            { name: 'Condenação', value: 200 },
            { name: 'Acordos', value: 100 },
        ])
    })
})

describe('alvarás', () => {
    const dias = [
        { data: '2026-01-05', quantidade: 2, valor: 10 },
        { data: '2026-01-07', quantidade: 1, valor: 5 },
        { data: '2025-01-05', quantidade: 9, valor: 9 },
    ]
    it('por mês e por dia do ano escolhido', () => {
        expect(alvarasPorMes(dias, '2026').qtd[0]).toBe(3)
        const d = alvarasPorDia(dias, '2026', 0)
        expect(d.dias).toBe(31)
        expect(d.qtd[4]).toBe(2)
        expect(d.valor[6]).toBe(5)
    })
    it('previsão = expedição + 5 dias úteis (sem fins de semana e feriados fixos)', () => {
        expect(previsaoCompensacao('2026-11-09')).toBe('2026-11-16') // seg -> seg seguinte
        expect(previsaoCompensacao('2026-11-12')).toBe('2026-11-19') // pula o 15/11 (domingo) e o fim de semana
        expect(previsaoCompensacao('2026-11-16')).toBe('2026-11-24') // pula o 20/11 (feriado)
        expect(diasUteisAte('2026-11-19', '2026-11-17')).toBe(2)
        expect(diasUteisAte('2026-11-17', '2026-11-17')).toBe(0)
        expect(diasUteisAte('2026-11-13', '2026-11-17')).toBeLessThan(0)
    })
})

describe('LA e RJ', () => {
    it('a linha CS (sem grau) só aparece quando já teve dado', () => {
        const r = resp()
        expect(series(lados(r, 'ambos')).temSemGrau).toBe(false)
        r.condenacao!.historico.execucao_entrada_fluxo_cs_por_mes_NG = [
            { name: 'jan 2025', '1G': 1, 'CS (sem grau)': 2 },
        ]
        const s = series(lados(r, 'ambos'))
        expect(s.temSemGrau).toBe(true)
        expect(s.fluxo.get('jan 2025')).toEqual({ '1G': 1, '2G': 0, 'CS (sem grau)': 2, Outros: 0 })
    })
    it('as atividades da Confecção CS vêm da resposta (a NG fica com as 4 da v1 sem o campo)', () => {
        expect(atividadesConfeccao({ meta })).toHaveLength(4)
        const la = execucaoEstrategicoFor('LA_AM')
        expect(atividadesConfeccao(la)[0]).toBe('Elaborar Cumprimento de Sentença')
        expect(estrategicoFilters(la).find((f) => f.key === 'atividade_execucao')?.options).toHaveLength(5)
        expect(execucaoEstrategicoFor('Consolidado').condenacao).toBeUndefined()
    })
})

describe('filtros e mock', () => {
    it('sem dados: nenhum filtro; com o mock: escopo, página, ano e Confecção CS', () => {
        expect(estrategicoFilters({ meta })).toEqual([])
        const chaves = estrategicoFilters(execucaoEstrategicoFor('NG')).map((f) => f.key)
        expect(chaves).toEqual([
            'escopo',
            'uf',
            'comarca',
            'materia',
            'subfase',
            'ano_ajuizamento',
            'atividade_execucao',
            'funcionario_execucao',
            'situacao_execucao',
        ])
    })
})
