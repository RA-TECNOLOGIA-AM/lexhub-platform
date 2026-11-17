import { describe, expect, it } from 'vitest'
import { acordosFilters } from './filters.ts'
import { ehAcordosNG, lerAcordosNG } from './execucaoAcordos.ts'

const meta = { unit: 'NG', from: '2026-11-01', to: '2026-11-17', source: 'LexFlow', synced_at: null, timezone: 'x' }

const resposta = {
    meta,
    dashboard: 'execucao_acordos_NG',
    stats: {
        total_em_execucao_acordos_NG: 520,
        valor_total_em_execucao_acordos_NG: 3_900_000,
        total_entrada_execucao_acordos_periodo_NG: 14,
        total_saida_execucao_acordos_periodo_NG: 9,
        valor_saida_execucao_acordos_periodo_NG: 61_000,
        tre_execucao_acordos_NG: 0.9,
        total_valor_alcada_final_vazio_acordos_NG: 1,
        total_valor_alcada_final_vazio_acordos_NG_detalhe: [{ numero_processo: '222' }],
        execucao_acordos_materia_opcoes_NG: ['CESTA'],
    },
    fechamento_acordo_por_subfase_NG: [{ name: 'ACORDO EM NEGOCIAÇÃO', value: 30 }],
    execucao_acordos_por_sentenca_NG: [
        { name: 'Pré-Sentença', value: 300 },
        { name: 'Pós-Sentença', value: 220 },
    ],
    execucao_acordos_por_tipo_acao_NG: [{ name: 'Judicial', value: 500 }],
    execucao_acordos_valor_por_comarca_saida_NG: [{ name: 'MANAUS', value: 61_000, uf: 'AM' }],
    quantidade_saida_execucao_acordos_por_mes_NG: [{ name: 'out 2026', value: 11 }],
    execucao_acordos_lista_saida_NG: [
        { id: 1, numero_processo: '333', uf: 'AM', data_execucao: '2026-03-01', valor_execucao: 5000, subfase: 'PAGO' },
    ],
    execucao_acordos_diligencias_por_processo_NG: [{ name: '333', value: 2, valor_execucao: 5000 }],
}

describe('lerAcordosNG', () => {
    it('lê as seções da página da v1', () => {
        const a = lerAcordosNG(resposta as never)
        expect(a.totalEmExecucao).toBe(520)
        expect(a.entradas).toBe(14)
        expect(a.pagos).toBe(9)
        expect(a.valorPagos).toBe(61_000)
        expect(a.tre).toBe(0.9)
        expect(a.semValor).toEqual({ total: 1, processos: ['222'] })
        expect(a.fechamentoPorSubfase).toEqual([{ name: 'ACORDO EM NEGOCIAÇÃO', value: 30 }])
        expect(a.porSentenca).toHaveLength(2)
        expect(a.comarca.saida.valor).toEqual([{ name: 'MANAUS', value: 61_000, uf: 'AM' }])
        expect(a.pagosPorMes).toEqual([{ name: 'out 2026', value: 11 }])
        expect(a.listas.saida).toEqual([
            { processo: '333', uf: 'AM', subfase: 'PAGO', dataExecucao: '2026-03-01', valor: 5000 },
        ])
        expect(a.listas.entrada).toEqual([])
        expect(a.setor.diligencias.porProcesso).toEqual([{ processo: '333', valor: 5000, quantidade: 2 }])
    })

    it('só a rota /execucao_acordos_NG é a da NG', () => {
        expect(ehAcordosNG(resposta as never)).toBe(true)
        expect(ehAcordosNG({ meta, dashboard: 'execucao_acordos_LA' })).toBe(false)
    })
})

describe('filtros dos Acordos', () => {
    it('NG: os da página (com as classificações e o processo, de um valor só) e os das seções', () => {
        const campos = acordosFilters(resposta as never)
        const pagina = campos.filter((c) => !c.inline).map((c) => c.key)
        expect(pagina).toEqual([
            'uf',
            'comarca',
            'materia',
            'subfase',
            'tipo_sentenca_execucao_acordos',
            'tipo_acao_execucao_acordos',
            'numero_processo_execucao_acordos',
        ])
        expect(campos.find((c) => c.key === 'tipo_sentenca_execucao_acordos')?.single).toBe(true)
        expect(campos.find((c) => c.key === 'numero_processo_execucao_acordos')?.options).toEqual([
            { value: '333', label: '333' },
        ])
        expect(campos.some((c) => c.key === 'funcionario_execucao_acordos' && c.inline)).toBe(true)
    })

    it('LA e RJ (tela de KPIs) não têm filtros', () => {
        expect(acordosFilters({ meta, dashboard: 'execucao_acordos_LA' })).toEqual([])
    })
})
