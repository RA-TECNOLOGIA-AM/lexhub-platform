import { describe, expect, it } from 'vitest'
import { estrategicoFor } from '../../../services/mock/estrategico.ts'
import {
    comarcasDisponiveis,
    comparativo,
    diasDoMes,
    divideSeries,
    numerosJuridico,
    brlSelo,
    gargalo,
    listaSubfases,
    pontosMapa,
    resumoFases,
    rotuloMes,
    semSubfase,
    subfases,
    unidadeMapa,
} from './estrategico.ts'
import { estrategicoFilters } from './filters.ts'

describe('Estratégico', () => {
    it('comparativo de valores já somados (v1: combinarComparativo); sem anterior, sem comparativo', () => {
        expect(comparativo(150, 100)).toBe(50)
        expect(comparativo(50, 100)).toBe(-50)
        expect(comparativo(10, 0)).toBeNull()
    })

    it('ticket médio por mês: valor ÷ protocolados do mesmo mês, sem os meses sem protocolado', () => {
        const valor = [
            { name: '2026-01', value: 300 },
            { name: '2026-02', value: 100 },
        ]
        const qtd = [
            { name: '2026-01', value: 3 },
            { name: '2026-02', value: 0 },
        ]
        expect(divideSeries(valor, qtd)).toEqual([{ name: '2026-01', value: 100 }])
    })

    it('os dias de um mês e o rótulo do mês', () => {
        const dias = [
            { name: '2026-11-03', value: 2 },
            { name: '2026-10-31', value: 1 },
            { name: '2026-11-01', value: 4 },
        ]
        expect(diasDoMes(dias, '2026-11').map((d) => d.name)).toEqual(['2026-11-01', '2026-11-03'])
        expect(rotuloMes('2026-03')).toBe('Março de 2026')
    })

    it('subfases da maior para a menor, com o total', () => {
        const s = subfases([
            { name: 'A', value: 1 },
            { name: 'B', value: 5 },
        ])
        expect(s.itens.map((i) => i.name)).toEqual(['B', 'A'])
        expect(s.total).toBe(6)
        expect(subfases(null)).toEqual({ itens: [], total: 0 })
    })

    it('números do Jurídico sem dado viram zero', () => {
        expect(numerosJuridico(undefined).execucaoValorExecucao).toBe(0)
    })

    it('filtros: UF só na NG; comarcas do Jurídico fixo em ordem', () => {
        const ng = estrategicoFor('NG')
        const la = estrategicoFor('LA_AM')
        expect(estrategicoFilters(ng).map((f) => f.key)).toEqual([
            'uf_estrategico',
            'comarca_estrategico',
            'situacao_estrategico',
        ])
        expect(estrategicoFilters(la).map((f) => f.key)).not.toContain('uf_estrategico')
        const comarcas = comarcasDisponiveis(ng)
        expect(comarcas[0]).toBe('BELÉM')
        expect(comarcas).toContain('MANAUS')
    })

    it('cards de fase: % do total das três fases e o selo da seção', () => {
        const r = resumoFases({
            ...estrategicoFor('NG').juridico_periodo!,
            fase_inicial_total_processos: 350,
            fase_recursal_total_processos: 540,
            fase_execucao_total_processos: 110,
            fase_inicial_valor_causa_total: 10,
            fase_recursal_valor_causa_total: 20,
            fase_execucao_valor_causa_total: 5,
        })
        expect(r.processos).toBe(1000)
        expect(r.valor).toBe(35)
        expect(r.fases.map((f) => f.pctTotal)).toEqual([35, 54, 11])
        expect(r.fases[0].secundario).toBeNull()
        expect(r.fases[1].secundario?.rotulo).toBe('Valor sentença')
        expect(resumoFases(undefined).fases.every((f) => f.pctTotal === 0)).toBe(true)
    })

    it('tabela de subfases: busca sem acento, ordens e gargalo de tempo médio', () => {
        const itens = [
            { name: 'AG. CITAÇÃO', value: 3, valor_causa: 900, tempo_medio_dias: 50 },
            { name: 'AG. DESPACHO', value: 341, valor_causa: 100, tempo_medio_dias: 84 },
            { name: 'SEM SUBFASE', value: 10 },
        ]
        const nomes = (o: Parameters<typeof listaSubfases>[2], b = '') =>
            listaSubfases(itens, 'valor_causa', o, b).map((s) => s.name)
        expect(nomes('processos')).toEqual(['AG. DESPACHO', 'SEM SUBFASE', 'AG. CITAÇÃO'])
        expect(nomes('valor')).toEqual(['AG. CITAÇÃO', 'AG. DESPACHO', 'SEM SUBFASE'])
        expect(nomes('tempo')).toEqual(['AG. DESPACHO', 'AG. CITAÇÃO', 'SEM SUBFASE'])
        expect(nomes('nome')[0]).toBe('AG. CITAÇÃO')
        expect(nomes('processos', 'citacao')).toEqual(['AG. CITAÇÃO'])
        expect(gargalo(itens)).toBe('AG. DESPACHO')
        expect(gargalo([{ name: 'X', value: 1 }])).toBeNull()
        expect(semSubfase(itens[2])).toBe(true)
    })

    it('selo com 2 casas em milhões', () => {
        expect(brlSelo(34_980_000).replace(/\s/g, ' ')).toBe('R$ 34,98 mi')
    })

    it('mapa: quantidade e valor de causa por comarca com a UF; unidade do mapa', () => {
        const p = pontosMapa([
            { name: 'BELÉM', value: 3, uf: 'PA', valor_causa: 900 },
            { name: 'Sem comarca', value: 1 },
        ])
        expect(p.quantidade).toEqual([
            { name: 'BELÉM', value: 3, uf: 'PA' },
            { name: 'Sem comarca', value: 1, uf: null },
        ])
        expect(p.valor[0]).toEqual({ name: 'BELÉM', value: 900, uf: 'PA' })
        expect(unidadeMapa('LA_AM')).toBe('LA')
        expect(unidadeMapa('RJ')).toBe('RJ')
        expect(unidadeMapa('NG')).toBe('NG')
    })
})
