import { describe, expect, it } from 'vitest'
import {
    agendaAgregada,
    comissaoEmendas,
    filtrosEmendas,
    geraComissao,
    lerEmendas,
    type EmendasResponse,
} from './emendas.ts'

const meta = { unit: 'NG', from: '2026-11-01', to: '2026-11-19', source: 'LexFlow', synced_at: null, timezone: 'x' }

const linha = (funcionario: string, extra: Record<string, unknown> = {}) => ({
    funcionario,
    agenda_finalizada: 9,
    agenda_total: 10,
    agenda_percentual: 90,
    elegivel: true,
    qtd_manifestacao: 4,
    valor_manifestacao: 1,
    qtd_dilacao: 2,
    valor_dilacao: 0.5,
    valor_comissao: 5,
    ...extra,
})

const resposta = (unidade: 'NG' | 'LA' | 'RJ', comissao: unknown[] = []): EmendasResponse => ({
    meta,
    unidade,
    stats: {
        total_atividades_emendas_manifestacoes_NG: 10,
        total_por_prazo_emendas_manifestacoes_NG: 7,
        comparativo_qtd_manifestacoes_emendas_manifestacoes_NG: -12.5,
        emendas_manifestacoes_uf_opcoes_NG: ['PA', 'AM'],
    },
    emendas_manifestacoes_comissionamento_por_funcionario_NG: comissao,
    emendas_manifestacoes_atividades_lista_filtros_opcoes_NG: { funcionarios: ['Bia', 'Ana'], atividades: ['X'] },
})

describe('lerEmendas', () => {
    it('as duas visões, o comparativo e as UFs (nomes da NG nas duas unidades)', () => {
        const e = lerEmendas(resposta('NG', [linha('Ana', { resolvidos_por_uf: [{ uf: 'AM', qtd_manifestacao: 3 }] })]))
        expect(e.visoes.concluidas.cards.total).toBe(10)
        expect(e.visoes.por_prazo.cards.total).toBe(7)
        expect(e.comparativo.manifestacoes).toBe(-12.5)
        expect(e.ufs).toEqual(['AM', 'PA'])
        expect(e.comissao[0].porUf).toEqual([{ uf: 'AM', manifestacao: 3, dilacao: 0 }])
    })
})

describe('agenda cumprida (o agregado da v1)', () => {
    it('soma de quem está na comissão; no LA, a faixa do conjunto', () => {
        const linhas = lerEmendas(
            resposta('LA', [
                linha('Ana', { agenda_finalizada: 96, agenda_total: 100 }),
                linha('Bia', { agenda_finalizada: 98, agenda_total: 100 }),
            ]),
        ).comissao
        const a = agendaAgregada(linhas, [])
        expect(a).toMatchObject({ rotulo: 'Todos os funcionários', percentual: 97, faixa: 'faixa_2', elegivel: true })
        expect(agendaAgregada(linhas.slice(0, 1), ['Ana'])).toMatchObject({ rotulo: 'Ana', faixa: 'faixa_1' })
        expect(agendaAgregada([], [])).toMatchObject({ temDados: false, elegivel: false, percentual: 0 })
    })
})

describe('o que gera comissão ("Por atividade")', () => {
    it('NG por exclusão; LA pela lista fechada', () => {
        expect(geraComissao('ELABORAR DILAÇÃO', 'NG')).toBe(true)
        expect(geraComissao('Análise de Manifestação', 'NG')).toBe(false)
        expect(geraComissao('DILAÇÃO DE PRAZO', 'LA')).toBe(true)
        expect(geraComissao('AVALIAR MANIFESTAÇÃO (INT)', 'LA')).toBe(false)
    })
})

describe('comissão (PDF)', () => {
    it('NG: valor fixo e uma coluna por UF (Sem UF por último)', () => {
        const t = comissaoEmendas(
            resposta('NG', [
                linha('Ana', {
                    resolvidos_por_uf: [
                        { uf: 'Sem UF', qtd_manifestacao: 1 },
                        { uf: 'PA', qtd_manifestacao: 2, qtd_dilacao: 1 },
                    ],
                }),
            ]),
        )!
        expect(t.title).toBe('Comissionamento — Emendas e Manifestações NG')
        expect(t.columns.map((c) => c.key)).toEqual([
            'funcionario',
            'agenda',
            'manifestacao_PA',
            'manifestacao_Sem UF',
            'qtd_manifestacao',
            'valor_manifestacao',
            'dilacao_PA',
            'dilacao_Sem UF',
            'qtd_dilacao',
            'valor_dilacao',
            'valor_comissao',
        ])
        expect(t.rows[0]).toMatchObject({
            manifestacao_PA: 2,
            dilacao_PA: 1,
            'manifestacao_Sem UF': 1,
            valor_comissao: 5,
        })
    })

    it('LA: a faixa de cada um (ou não elegível), maior comissão primeiro', () => {
        const t = comissaoEmendas(
            resposta('LA', [
                linha('Bia', { elegivel: false, valor_comissao: 0 }),
                linha('Ana', { faixa: 'faixa_2', valor_comissao: 9 }),
            ]),
        )!
        expect(t.rows.map((r) => [r.funcionario, r.faixa])).toEqual([
            ['Ana', 'Faixa 2'],
            ['Bia', 'Não elegível'],
        ])
    })

    it('sem linhas: sem comissão', () => {
        expect(comissaoEmendas(resposta('NG'))).toBeUndefined()
    })
})

describe('filtros', () => {
    it('UF só no NG; atividade vem do gráfico', () => {
        expect(filtrosEmendas(resposta('NG')).map((f) => f.key)).toEqual([
            'funcionario_emendas_manifestacoes',
            'uf_emendas_manifestacoes',
            'atividade_emendas_manifestacoes',
            'situacao_processo',
        ])
        expect(filtrosEmendas(resposta('LA')).map((f) => f.key)).not.toContain('uf_emendas_manifestacoes')
    })
})

describe('RJ (sem página na v1: as regras do NG)', () => {
    it('UF, valor fixo e as cores do NG, com o RJ no título', () => {
        const r = resposta('RJ', [linha('Ana', { resolvidos_por_uf: [{ uf: 'RJ', qtd_manifestacao: 4 }] })])
        const e = lerEmendas(r)
        expect([e.unidade, e.regra]).toEqual(['RJ', 'NG'])
        expect(filtrosEmendas(r).map((f) => f.key)).toContain('uf_emendas_manifestacoes')
        const t = comissaoEmendas(r)!
        expect(t.title).toBe('Comissionamento — Emendas e Manifestações RJ')
        expect(t.columns.map((c) => c.key)).toContain('manifestacao_RJ')
        expect(t.notes?.at(-1)).toContain('Manifestar dilação de prazo')
    })
})
