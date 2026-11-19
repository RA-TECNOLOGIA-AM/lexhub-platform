import type { ControleResponse } from '../../pages/dashboards/controle-processos/controle.ts'
import type { DashboardQuery } from '../../types/index.ts'
import { metaFor } from './helpers.ts'

// Controle de Processos fictício (NG, LA e RJ; os mesmos números), no formato da resposta da V2 (app/dashboards/controle_processos.py).
// Números inventados, determinísticos.

const FASES: [string, number][] = [
    ['INICIAL', 7800],
    ['RECURSAL', 5450],
    ['SEM FASE', 2620],
    ['EXECUÇÃO', 487],
    ['SUSPENSO', 215],
    ['ACORDO', 147],
    ['ARQUIVADO POR PROCEDÊNCIA', 122],
]
const SUBFASES = [
    'AG. DESPACHO INICIAL',
    'AG. CITAÇÃO',
    'AG. AUDIÊNCIA',
    'AG. SENTENÇA',
    'AG. CONTESTAÇÃO',
    'AG. RÉPLICA',
]

function serie(base: number) {
    const out: { name: string; value: number }[] = []
    const meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    for (const ano of [2025, 2026])
        meses.forEach((m, i) => {
            if (ano === 2026 && i > 10) return
            out.push({ name: `${m} ${ano}`, value: Math.round(base + 40 * Math.sin(i + ano)) })
        })
    return out
}

export function controleFor(unit: string, query?: DashboardQuery): ControleResponse {
    const meta = metaFor(unit, 'LexFlow')
    const unidade = ({ NG: 'NG', LA: 'LA', LA_AM: 'LA', RJ: 'RJ', LA_RJ: 'RJ' } as Record<string, string>)[unit]
    if (!unidade) return { meta }
    const fase = query?.filters?.fase_controle?.[0]
    const totalFase = FASES.find(([f]) => f === fase)?.[1] ?? 0
    const c = (k: string) => `controle_processo_${k}_NG`
    return {
        meta,
        unidade,
        tem_uf: unidade !== 'LA',
        periodo: {
            [c('fase_inicial_media_dias')]: 204.48,
            [c('fase_recursal_media_dias')]: 71.7,
            [c('fase_execucao_media_dias')]: 43.09,
            [c('fase_inicial_mediana_dias')]: 170,
            [c('fase_recursal_mediana_dias')]: 46.81,
            [c('fase_execucao_mediana_dias')]: 29.98,
            [c('fase_inicial_comparativo_media_dias')]: -0.68,
            [c('fase_recursal_comparativo_media_dias')]: 1.88,
            [c('fase_execucao_comparativo_media_dias')]: -46.83,
            [c('fase_inicial_comparativo_mediana_dias')]: 0.19,
            [c('fase_recursal_comparativo_mediana_dias')]: -27.62,
            [c('fase_execucao_comparativo_mediana_dias')]: -65.96,
            [c('extintos_com_merito_qtd')]: 191,
            [c('extintos_com_merito_valor_causa')]: 4_740_052.34,
            [c('extintos_com_merito_2g_qtd')]: 114,
            [c('extintos_com_merito_2g_valor_causa')]: 2_675_245.53,
            [c('extintos_sem_merito_qtd')]: 70,
            [c('extintos_sem_merito_valor_causa')]: 2_036_353.93,
            [c('extintos_sem_merito_2g_qtd')]: 16,
            [c('extintos_sem_merito_2g_valor_causa')]: 512_445.06,
            [c('fase_arquivado_improcedente_qtd')]: 0,
            [c('fase_arquivado_improcedente_valor_causa')]: 0,
            [c('taxa_provimento_2g')]: 35.8,
            [c('extintos_com_merito_por_tipo_sentenca')]: [
                { tipo_sentenca: 'SENTENÇA PROCEDENTE', quantidade: 120, valor_causa: 2_900_000 },
                { tipo_sentenca: 'SENTENÇA IMPROCEDENTE', quantidade: 71, valor_causa: 1_840_052.34 },
            ],
            [c('extintos_com_merito_2g_por_tipo_sentenca')]: [
                { tipo_sentenca: 'RECURSO PROVIDO', quantidade: 64, valor_causa: 1_500_000 },
                { tipo_sentenca: 'RECURSO NÃO PROVIDO', quantidade: 50, valor_causa: 1_175_245.53 },
            ],
        },
        historico: {
            total_controle_processo_NG: 17083,
            [c('valor_causa_total')]: 423_186_546.37,
            [c('fase_inicial_qtd')]: 7799,
            [c('fase_inicial_valor_causa')]: 208_391_434.55,
            [c('log_inicial_indeferida_qtd')]: 12,
            [c('log_inicial_indeferida_valor_causa')]: 310_000,
            [c('fase_recursal_qtd')]: 5450,
            [c('fase_recursal_valor_causa')]: 133_369_967.37,
            [c('log_recursal_nao_provido_qtd')]: 41,
            [c('log_recursal_nao_provido_valor_causa')]: 980_000,
            [c('fase_transito_julgado_qtd')]: 6,
            [c('fase_transito_julgado_valor_causa')]: 95_211.45,
            [c('uf_opcoes')]: ['AM', 'PA', 'PB'],
            [c('por_fase')]: FASES.map(([name, value]) => ({ name, value })),
            [c('fase_inicial_media_dias_por_mes')]: serie(210),
            [c('fase_recursal_media_dias_por_mes')]: serie(80),
            [c('fase_execucao_media_dias_por_mes')]: serie(60),
        },
        fase: fase
            ? {
                  [c('por_subfase')]: SUBFASES.map((name, i) => ({
                      name,
                      value: Math.round(totalFase / (i + 2)),
                      valor_causa: Math.round(totalFase / (i + 2)) * 26_000,
                      ...(i % 3 !== 2 ? { tempo_medio_dias: 20 + i * 17.5 } : {}),
                  })),
                  [c('qtd_subfases_na_fase')]: SUBFASES.length,
                  [c('total_na_fase')]: SUBFASES.reduce((s, _, i) => s + Math.round(totalFase / (i + 2)), 0),
              }
            : null,
        protocolo: {
            protocolos_resolvidos: 0,
            valor_causa_protocolo_novo: 0,
            tempo_medio_contratacao_protocolo: 18.4,
            mediana_tempo_contratacao_protocolo: 12,
            comparativo_tempo_medio_contratacao_protocolo: 5.2,
            comparativo_mediana_tempo_contratacao_protocolo: -3.1,
        },
        lexpre: {
            protocolados_total: 259,
            valor_causa_protocolado: 6_076_284.79,
            media_tempo_protocolado: 0.33,
            mediana_tempo_protocolado: 0.06,
            comparativo_tempo_medio_protocolado: -65.62,
            comparativo_mediana_tempo_protocolado: -14.29,
        },
        execucao: {
            total_saida_execucao_periodo: 50,
            valor_ted_saida_execucao_periodo: 659_600.58,
            total_saida_execucao_acordos_periodo_NG: 34,
            valor_ted_saida_execucao_acordos_periodo_NG: 282_168.77,
            total_em_execucao: 463,
            valor_total_em_execucao: 4_907_856.42,
            total_em_execucao_acordos_NG: 145,
            valor_total_em_execucao_acordos_NG: 1_140_752.57,
        },
    }
}
