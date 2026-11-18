import { describe, expect, it } from 'vitest'
import { commissionHtml } from '../../../lib/commissionReport.ts'
import {
    celulaMarcada,
    clicarCelula,
    comissaoRecursal,
    filtroDecisao,
    lerRecursal,
    porTipo,
    producaoDias,
    tomTaxa,
    type RecursalResponse,
} from './recursal.ts'
import { recursalFilters } from './filters.ts'
import { recursalFor } from '../../../services/mock/recursal.ts'

const meta = { unit: 'NG' } as unknown as RecursalResponse['meta']

describe('decisões e matriz 1º × 2º grau', () => {
    it('o card Extinção filtra com o id que a API aceita', () => {
        expect(filtroDecisao('extincao_reajuizar')).toBe('extincao_permite_reajuizar')
        expect(filtroDecisao('mantido_ganho')).toBe('mantido_ganho')
    })
    it('clicar numa célula troca decisão e status 1G/2G; de novo, tira os três', () => {
        const f = clicarCelula({ juiz_recursal: ['X'] }, 0, 0)
        expect(f).toEqual({
            juiz_recursal: ['X'],
            decisao_recursal: ['mantido_ganho'],
            id_1g_recursal: ['20'],
            id_2g_recursal: ['21'],
        })
        expect(celulaMarcada(f, 0, 0)).toBe(true)
        expect(clicarCelula(f, 0, 0)).toEqual({ juiz_recursal: ['X'] })
    })
    it('linha/coluna sem id antigo (prescrição) não manda o status daquela dimensão', () => {
        const f = clicarCelula({}, 5, 6)
        expect(f).toEqual({ decisao_recursal: ['extincao_permite_reajuizar'], id_2g_recursal: ['18'] })
        expect(celulaMarcada(f, 5, 6)).toBe(true)
    })
})

describe('contas da página da v1', () => {
    it('cor da taxa de sucesso', () => {
        expect([tomTaxa(60), tomTaxa(45), tomTaxa(44.9)]).toEqual(['ok', 'warn', 'danger'])
    })
    it('extintos por tipo: lista ou objeto', () => {
        expect(porTipo([{ label: 'IMPROCEDENTE', quantidade: 3, valor_causa: 10 }, { label: '' }])).toEqual([
            { tipo: 'IMPROCEDENTE', qtd: 3, valor: 10 },
        ])
        expect(porTipo({ A: 2 })).toEqual([{ tipo: 'A', qtd: 2, valor: null }])
    })
    it('produção: um funcionário, vários (soma) ou o setor', () => {
        const producao = {
            recursal_resolvidos_por_dia_NG: [{ name: '2026-11-03', value: 9 }],
            recursal_resolvidos_por_dia_por_funcionario_NG: {
                Ana: [{ name: '2026-11-03', value: 2 }],
                Bia: [{ name: '2026-11-03', value: 3 }],
            },
        }
        expect(producaoDias(producao, ['Ana'])).toEqual([{ name: '2026-11-03', value: 2 }])
        expect(producaoDias(producao, ['Ana', 'Bia'])).toEqual([{ name: '2026-11-03', value: 5 }])
        expect(producaoDias(producao, [])).toEqual([{ name: '2026-11-03', value: 9 }])
    })
    it('LA sem Cancelados e sem Meta de provimento; NG com os dois', () => {
        const la = lerRecursal(recursalFor('LA_AM'))
        expect(la.cancelados).toBeNull()
        expect(la.provimento).toBeNull()
        const ng = lerRecursal(recursalFor('NG'))
        expect(ng.cancelados).toBe(5)
        expect(ng.provimento?.pct).toBeCloseTo(77.5)
        expect(ng.extintos.seguemFiltros).toBe(false)
        expect(lerRecursal(recursalFor('LA_RJ')).extintos.seguemFiltros).toBe(true)
    })
    it('meta de provimento padrão 80 e demandas ordenadas pelo total', () => {
        const r = lerRecursal({
            meta,
            periodo: {
                stats: { provimento_mensal_qtd_NG: 40 },
                recursal_demandas_por_funcionario_NG: [
                    { name: 'A', encerrado_cumprido: 1, encerrado_nao_cumprido: 1 },
                    { name: 'B', encerrado_cumprido: 5, encerrado_nao_cumprido: 0 },
                ],
            },
        })
        expect(r.provimento).toEqual({ qtd: 40, meta: 80, pct: 50 })
        expect(r.demandas.map((d) => d.name)).toEqual(['B', 'A'])
    })
})

describe('filtros', () => {
    it('sem dados: nenhum; com o mock: os da página da v1 na ordem do painel', () => {
        expect(recursalFilters({ meta })).toEqual([])
        expect(recursalFilters(recursalFor('NG')).map((f) => f.key)).toEqual([
            'id_1g_recursal',
            'id_2g_recursal',
            'decisao_recursal',
            'juiz_recursal',
            'relator_recursal',
            'materia_recursal',
            'competencia_recursal',
            'vara_recursal',
            'subfase_recursal',
            'extinto_2g_recursal',
            'funcionario_recursos',
            'atividade_recursos',
            'situacao_recursos',
            'status_recursos',
            'situacao_processo',
        ])
    })
    it('o escolhido continua na lista mesmo sem estar nas opções de agora', () => {
        const f = recursalFilters(recursalFor('NG'), { juiz_recursal: ['Fora da lista'] })
        expect(f.find((x) => x.key === 'juiz_recursal')?.options.some((o) => o.value === 'Fora da lista')).toBe(true)
    })
})

describe('relatório de comissão do setor Recursos', () => {
    it('só NG (LA, RJ ou sem o bloco: sem comissão)', () => {
        expect(comissaoRecursal(recursalFor('LA_AM'))).toBeUndefined()
        expect(comissaoRecursal(recursalFor('LA_RJ'))).toBeUndefined()
        expect(comissaoRecursal({ meta })).toBeUndefined()
    })
    it('resumo como a v1: erros com o desconto, subsetores juntos e a meta de qualidade', () => {
        const t = comissaoRecursal(recursalFor('NG'))!
        expect(t.title).toBe('Relatório de Comissão — Setor Recursos (NG)')
        expect(t.notes?.[0]).toMatch(/^Meta de qualidade: não atingida \(62\/80 processos providos\)$/)
        const bruno = t.rows.find((r) => r.erros_analise !== '—')!
        expect(bruno.erros_analise).toBe('2 (-R$\u00a01,00)'.replace('1,00', '2,00'))
        expect(t.rows[0].subsetores).toBe('Análise + Confecção')
        expect(t.details?.rows).toHaveLength(2)
        expect(t.details?.rows[0].desconto).toBe('-R$\u00a01,00')
    })
    it('o HTML traz o detalhamento numa página nova', () => {
        const t = comissaoRecursal(recursalFor('NG'))!
        const html = commissionHtml({
            ...t,
            title: t.title!,
            unit: 'NG',
            from: '2026-11-01',
            to: '2026-11-18',
            generatedAt: new Date(0),
        })
        expect(html).toContain('Detalhamento dos descontos por erro')
        expect(html).toContain('class="detalhes"')
        expect(html).toContain('Meta de qualidade')
    })
})
