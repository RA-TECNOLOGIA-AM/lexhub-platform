import { describe, expect, it } from 'vitest'
import {
    VALOR_FAIXA,
    comissaoIntermediarias,
    diasDosFuncionarios,
    faixaIndividual,
    filtrosIntermediarias,
    lerIntermediarias,
    type PendenciasIntermediariasResponse,
} from './intermediarias.ts'

const meta = { unit: 'NG', from: '2026-11-01', to: '2026-11-19', source: 'LexFlow', synced_at: null, timezone: 'x' }

const resposta = (extra: Record<string, unknown> = {}): PendenciasIntermediariasResponse => ({
    meta,
    unidade: 'LA',
    stats: {
        total_atividades_intermediarias_NG: 10,
        total_por_prazo_intermediarias_NG: 7,
        por_prazo_concluidas_intermediarias_NG: 3,
        dilacoes_intermediarias_taxa_NG: 4.2,
        dilacoes_intermediarias_count_NG: 2,
        dilacoes_intermediarias_total_encerrados_NG: 48,
        dilacoes_intermediarias_faixa_NG: 'ouro',
    },
    intermediarias_demandas_por_funcionario_NG: [
        { name: 'Ana', encerrado_cumprido: 2, encerrado_nao_cumprido: 1, total: 3 },
        { name: 'Bia', encerrado_cumprido: 9, encerrado_nao_cumprido: 0, total: 9 },
    ],
    intermediarias_concluidas_por_dia_NG: [{ name: '2026-11-03', value: 5 }],
    intermediarias_concluidas_por_dia_por_funcionario_NG: {
        Ana: [
            { name: '2026-11-03', value: 2 },
            { name: '2026-11-04', value: 1 },
        ],
        Bia: [{ name: '2026-11-03', value: 3 }],
    },
    intermediarias_atividades_lista_filtros_opcoes_NG: { funcionarios: ['Bia', 'Ana'], atividades: ['X'] },
    intermediarias_por_prazo_lista_filtros_opcoes_NG: { funcionarios: ['Caio', 'Ana'], atividades: ['Y'] },
    ...extra,
})

describe('lerIntermediarias', () => {
    it('lê as duas visões com os nomes da NG (a API troca os do LA)', () => {
        const p = lerIntermediarias(resposta())
        expect(p.unidade).toBe('LA')
        expect(p.visoes.concluidas.cards.total).toBe(10)
        expect(p.visoes.por_prazo.cards).toMatchObject({ total: 7, concluidas: 3 })
        expect(p.visoes.concluidas.porFuncionario.map((f) => f.name)).toEqual(['Bia', 'Ana'])
        expect(p.dilacao).toEqual({ count: 2, totalEncerrados: 48, taxa: 4.2, faixa: 'ouro' })
        expect(p.funcionarios).toEqual(['Ana', 'Bia', 'Caio'])
        expect(p.atividades).toEqual(['X', 'Y'])
    })

    it('sem resposta: sem dados e sem filtros', () => {
        expect(lerIntermediarias({ meta }).temDados).toBe(false)
        expect(filtrosIntermediarias({ meta })).toEqual([])
    })
})

describe('histórico por funcionário (somado no navegador, como a v1)', () => {
    const v = lerIntermediarias(resposta()).visoes.concluidas
    it('sem filtro: a série do setor', () => {
        expect(diasDosFuncionarios(v, [])).toEqual([{ name: '2026-11-03', value: 5 }])
    })
    it('com filtro: soma as séries de quem foi escolhido', () => {
        expect(diasDosFuncionarios(v, ['Ana', 'Bia'])).toEqual([
            { name: '2026-11-03', value: 5 },
            { name: '2026-11-04', value: 1 },
        ])
        expect(diasDosFuncionarios(v, ['Ninguém'])).toEqual([])
    })
})

describe('comissão por dilação', () => {
    it('faixa individual da v1', () => {
        expect(faixaIndividual(0, 10)).toBe('ouro')
        expect(faixaIndividual(5, 10)).toBe('ouro')
        expect(faixaIndividual(5.1, 10)).toBe('prata')
        expect(faixaIndividual(10, 10)).toBe('prata')
        expect(faixaIndividual(15, 10)).toBe('bronze')
        expect(faixaIndividual(15.1, 10)).toBeNull()
        expect(faixaIndividual(0, 0)).toBeNull()
        expect(VALOR_FAIXA).toEqual({ bronze: 0.5, prata: 1, ouro: 2 })
    })

    it('só quem resolveu algo, valor = resolvidas × valor da faixa, por nome', () => {
        const t = comissaoIntermediarias(
            resposta({
                dilacoes_intermediarias_por_funcionario_NG: [
                    {
                        funcionario: 'Zeca',
                        qtd_dilacoes: 1,
                        total_encerrados: 8,
                        qtd_resolvidos: 6,
                        taxa_dilacao: 12.5,
                    },
                    { funcionario: 'Ana', qtd_dilacoes: 0, total_encerrados: 20, qtd_resolvidos: 18, taxa_dilacao: 0 },
                    { funcionario: 'Lia', qtd_dilacoes: 3, total_encerrados: 3, qtd_resolvidos: 0, taxa_dilacao: 100 },
                ],
            }),
        )!
        expect(t.title).toBe('Comissionamento — Pendências Intermediárias LA')
        expect(t.rows).toEqual([
            {
                funcionario: 'Ana',
                qtd_resolvidos: 18,
                qtd_dilacoes: 0,
                taxa_dilacao: 0,
                comissao_unitaria: 2,
                valor_comissao: 36,
            },
            {
                funcionario: 'Zeca',
                qtd_resolvidos: 6,
                qtd_dilacoes: 1,
                taxa_dilacao: 12.5,
                comissao_unitaria: 0.5,
                valor_comissao: 3,
            },
        ])
        expect(t.notes?.at(-1)).toBe('Taxa de dilação do setor no período (informativo): 4,2%')
    })

    it('sem ninguém com resolvidas: sem comissão (o botão some)', () => {
        expect(comissaoIntermediarias(resposta())).toBeUndefined()
    })
})

describe('filtros', () => {
    it('funcionários, atividade (vem do gráfico) e situação do processo; o escolhido continua na lista', () => {
        const f = filtrosIntermediarias(resposta(), { funcionario_intermediarias: ['Zeca'] })
        expect(f.map((x) => x.key)).toEqual([
            'funcionario_intermediarias',
            'atividade_intermediarias',
            'situacao_processo',
        ])
        expect(f[0].options.map((o) => o.value)).toEqual(['Ana', 'Bia', 'Caio', 'Zeca'])
        expect(f[1].fromChart).toBe(true)
    })
})
