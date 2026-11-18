import { describe, expect, it } from 'vitest'
import {
    comissaoPublicacoes,
    demandas,
    duracaoHoras,
    lerPublicacoes,
    linhaDoTempo,
    resolucao,
    statusAgendamento,
    type PublicacoesResponse,
} from './publicacoes.ts'
import { publicacoesFilters } from './filters.ts'
import { publicacoesFor } from '../../../services/mock/publicacoes.ts'

const meta = { unit: 'NG', from: '2026-11-01', to: '2026-11-04' } as unknown as PublicacoesResponse['meta']

describe('contas da página da v1', () => {
    it('linha do tempo: um ponto por dia; atraso = dias até o dia de referência onde há pendente', () => {
        const l = linhaDoTempo(
            {
                meta,
                stats: { dia_referencia_publicacoes_NG: '2026-11-04' },
                publicacoes_recebidas_por_dia_NG: [{ name: '2026-11-02', value: 5 }],
                publicacoes_tratadas_por_dia_NG: [{ name: '2026-11-03', value: 4 }],
                publicacoes_visualizadas_por_dia_NG: [],
                publicacoes_pendentes_por_dias_atraso_NG: [
                    { name: '0', value: 3 },
                    { name: '2', value: 1 },
                    { name: '1', value: 0 },
                ],
            },
            '2026-11-01',
            '2026-11-04',
        )
        expect(l.dias).toEqual(['2026-11-01', '2026-11-02', '2026-11-03', '2026-11-04'])
        expect(l.series.map((s) => s.label)).toEqual(['Chegadas', 'Cumpridas', 'Visualizadas', 'Atraso em dias'])
        expect(l.series[0].values).toEqual([0, 5, 0, 0])
        expect(l.series[3].values).toEqual([0, 2, 0, 0])
        expect(l.temDados).toBe(true)
    })
    it('LA: sem a série Visualizadas', () => {
        const l = linhaDoTempo({ meta, publicacoes_recebidas_por_dia_NG: [] }, '2026-11-01', '2026-11-02')
        expect(l.series.map((s) => s.label)).toEqual(['Chegadas', 'Cumpridas', 'Atraso em dias'])
        expect(l.temDados).toBe(false)
    })
    it('demandas: pendentes + cumpridas por leitor, maior total primeiro', () => {
        expect(
            demandas({
                meta,
                publicacoes_pendentes_por_leitor_NG: [{ name: 'A', value: 2 }],
                publicacoes_cumprido_por_leitor_NG: [
                    { name: 'A', value: 1 },
                    { name: 'B', value: 9 },
                ],
            }),
        ).toEqual([
            { name: 'B', pendentes: 0, cumpridas: 9, total: 9 },
            { name: 'A', pendentes: 2, cumpridas: 1, total: 3 },
        ])
    })
    it('taxa de resolução: comissiona a partir de 98%', () => {
        expect(resolucao(100, 98).comissiona).toBe(true)
        expect(resolucao(100, 97).comissiona).toBe(false)
        expect(resolucao(0, 5)).toMatchObject({ temDados: false, taxa: 0 })
        expect(resolucao(100, 120).pctCumpridas).toBe(100)
    })
    it('duração e o com/sem agendamento da fatia', () => {
        expect(duracaoHoras(0.22 * 24)).toBe('5h 17min')
        expect(duracaoHoras(0.5)).toBe('30min')
        expect(statusAgendamento('Sem agendamento')).toBe('sem')
        expect(statusAgendamento('Com agendamento')).toBe('com')
    })
})

describe('resposta, filtros e comissão', () => {
    it('lê o mock: agendamento com %, lista e leitores', () => {
        const p = lerPublicacoes(publicacoesFor('NG'))
        expect(p.agendamento.pct).toBeCloseTo(67, 0)
        expect(p.lista.length).toBe(42)
        expect(p.leitores[0]).toBe('SEM LEITOR')
    })
    it('filtros: leitor e matéria na janela; os dos gráficos só por clique', () => {
        expect(publicacoesFilters({ meta })).toEqual([])
        const f = publicacoesFilters(publicacoesFor('NG'))
        expect(f.map((x) => x.key)).toEqual([
            'leitor_publicacoes',
            'materia_publicacoes',
            'documento_publicacoes',
            'tribunal_publicacoes',
            'orgao_publicacoes',
            'atividade_agendamento_publicacoes',
            'setor_agendamento_publicacoes',
            'status_agendamento_publicacoes',
            'situacao_processo',
        ])
        expect(f[0].options[0]).toEqual({ value: 'SEM LEITOR', label: 'Sem leitor' })
        expect(f.filter((x) => x.fromChart).every((x) => x.single)).toBe(true)
    })
    it('comissão: R$ 0,20 por certa e R$ 0,50 por errada; sem o bloco, sem botão', () => {
        const t = comissaoPublicacoes(publicacoesFor('LA_AM'))!
        expect(t.title).toBe('Comissionamento — Publicações LA')
        expect(t.columns.map((c) => c.key)).toEqual([
            'funcionario',
            'qtd_lidas',
            'qtd_certas',
            'qtd_erradas',
            'valor_certa',
            'valor_errada',
            'comissao',
        ])
        expect(comissaoPublicacoes({ meta })).toBeUndefined()
    })
})
