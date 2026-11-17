import { describe, expect, it } from 'vitest'
import { lerExecucao } from './execucao.ts'

const meta = { unit: 'NG', from: '2026-11-01', to: '2026-11-17', source: 'LexFlow', synced_at: null, timezone: 'x' }

describe('lerExecucaoNG', () => {
    it('separa o total de agora (histórico) da entrada no período e lê as seções da v1', () => {
        const e = lerExecucao({
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
        const e = lerExecucao({ meta, dashboard: 'execucao' })
        expect(e.totalEmExecucao).toBeNull()
        expect(e.semValor).toEqual({ total: 0, processos: [] })
        expect(e.setor.atividades.concluidas.lista).toEqual([])
    })

    it('LA e RJ: os mesmos campos com o sufixo da rota (_LA, _RJ), como a v1', () => {
        const la = lerExecucao({
            meta,
            dashboard: 'execucao_LA',
            stats: {
                total_em_execucao_LA: 7, // entradas no período
                total_em_execucao_historico: 900, // o total de agora tem o mesmo nome nas três
                tre_LA: 1.5,
                total_valor_execucao_vazio_LA: 1,
                total_valor_execucao_vazio_LA_detalhe: [{ numero_processo: '9' }],
                execucao_uf_opcoes_LA: ['AM'],
                total_atividades_execucao_LA: 40,
                total_em_execucao: 99, // da NG: não é lido na LA
            },
            execucao_por_subfase_LA: [{ name: 'ALVARÁ', value: 2 }],
            execucao_resolvidos_por_dia_LA: [{ name: '2026-11-03', value: 4 }],
        } as never)
        expect(la.unidade).toBe('LA')
        expect(la.entradas).toBe(7)
        expect(la.totalEmExecucao).toBe(900)
        expect(la.tre).toBe(1.5)
        expect(la.semValor).toEqual({ total: 1, processos: ['9'] })
        expect(la.opcoes.ufs).toEqual(['AM'])
        expect(la.porSubfase).toEqual([{ name: 'ALVARÁ', value: 2 }])
        expect(la.setor.atividades.concluidas.total).toBe(40)
        expect(la.setor.atividades.concluidas.resolvidosPorDia).toEqual([{ name: '2026-11-03', value: 4 }])

        const rj = lerExecucao({
            meta,
            dashboard: 'execucao_RJ',
            stats: { total_diligencias_execucao_RJ: 5 },
            execucao_diligencias_por_funcionario_RJ: [{ name: 'Ana', total: 3 }],
        } as never)
        expect(rj.unidade).toBe('RJ')
        expect(rj.setor.diligencias.total).toBe(5)
        expect(rj.setor.diligencias.porColaborador).toEqual([{ name: 'Ana', value: 3 }])
    })
})
