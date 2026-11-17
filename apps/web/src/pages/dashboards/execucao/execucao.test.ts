import { describe, expect, it } from 'vitest'
import { ehExecucaoNG, lerExecucaoNG } from './execucao.ts'

const meta = { unit: 'NG', from: '2026-11-01', to: '2026-11-17', source: 'LexFlow', synced_at: null, timezone: 'x' }

describe('lerExecucaoNG', () => {
    it('separa o total de agora (histórico) da entrada no período e lê as seções da v1', () => {
        const e = lerExecucaoNG({
            meta,
            dashboard: 'execucao',
            stats: {
                total_em_execucao: 12, // com período: entradas
                total_em_execucao_historico: 3108, // sem período: total de agora
                valor_total_em_execucao: 42_000_000,
                valor_em_execucao: 90_000,
                total_saida_execucao_periodo: 7,
                total_incontroverso_saida_execucao_periodo: 2,
                tre: -1.25,
                total_valor_execucao_vazio: 2,
                total_valor_execucao_vazio_detalhe: [{ numero_processo: '111', campo: 'Valor da Execução' }],
                execucao_uf_opcoes_NG: ['AM', 'PA'],
                execucao_subfase_opcoes_NG: ['ALVARÁ'],
            },
            execucao_por_subfase: [{ name: 'ALVARÁ', value: 4 }],
            execucao_por_comarca_entrada: [{ name: 'MANAUS', value: 3, uf: 'AM', tempo_medio_dias: 120.5 }],
            valor_execucao_saida_periodo_por_mes: [{ name: 'nov 2026', value: 10 }],
            execucao_atividades_lista_NG: [],
        } as never)
        expect(e.totalEmExecucao).toBe(3108)
        expect(e.entradas).toBe(12)
        expect(e.valorTotal).toBe(42_000_000)
        expect(e.saidasIncontroverso).toBe(2)
        expect(e.tre).toBe(-1.25)
        expect(e.semValor).toEqual({ total: 2, processos: ['111'] })
        expect(e.porSubfase).toEqual([{ name: 'ALVARÁ', value: 4 }])
        expect(e.comarca.entrada.quantidade).toEqual([{ name: 'MANAUS', value: 3, uf: 'AM', tempoMedio: 120.5 }])
        expect(e.comarca.total.quantidade).toEqual([])
        expect(e.valorSaidasPorMes).toEqual([{ name: 'nov 2026', value: 10 }])
        expect(e.opcoes.ufs).toEqual(['AM', 'PA'])
        expect(e.opcoes.subfases).toEqual(['ALVARÁ'])
        expect(e.opcoes.comarcas).toEqual([])
    })

    it('resposta vazia (mock, campo faltando): números null e listas vazias', () => {
        const e = lerExecucaoNG({ meta, dashboard: 'execucao' })
        expect(e.totalEmExecucao).toBeNull()
        expect(e.semValor).toEqual({ total: 0, processos: [] })
        expect(e.setor.atividades.concluidas.lista).toEqual([])
    })

    it('só a rota /execucao é a da NG (LA e RJ seguem na tela de KPIs)', () => {
        expect(ehExecucaoNG({ meta, dashboard: 'execucao' })).toBe(true)
        expect(ehExecucaoNG({ meta, dashboard: 'execucao_LA' })).toBe(false)
        expect(ehExecucaoNG({ meta })).toBe(false)
    })
})
