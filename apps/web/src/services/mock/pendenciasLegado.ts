import type { V1GenericoResponse } from '../../pages/dashboards/v1Stats.ts'
import type { DashboardQuery, Point } from '../../types/index.ts'
import { metaFor } from './helpers.ts'

// Pendências (banco legado) fictícias, na ordem de grandeza das telas da v1 (novembro/2026): NG e LA_RJ no
// formato da rota /pendencias; LA_AM no da /pendencia_LA (nomes com _LA, sem reajuizamento nem comparativos).

const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
const NG_2024 = [null, null, null, null, null, null, 52, 34, 66, 117, 93, 132]
const NG_2025 = [92, 154, 87, 39, 11, 4, 38, 40, 33, 95, 117, 127]
const NG_2026 = [98, 108, 228, 118, 106, 134, 219, 72, 30, 22, 6, null]
const LA_2024 = [null, null, null, null, null, null, null, null, null, null, null, 10]
const LA_2025 = [182, 221, 319, 296, 202, 143, 305, 215, 239, 288, 295, 142]
const LA_2026 = [272, 252, 243, 206, 219, 199, 260, 215, 116, 17, 3, null]

function porMes(series: [number, (number | null)[]][]): Point[] {
    const out: Point[] = []
    for (const [ano, vs] of series)
        vs.forEach((v, i) => v !== null && out.push({ name: `${MESES[i]} ${ano}`, value: v }))
    return out
}

function porDia(query: DashboardQuery, base: number): Point[] {
    const de = new Date(`${query.from ?? '2026-10-01'}T12:00:00`)
    const ate = new Date(`${query.to ?? '2026-10-31'}T12:00:00`)
    const out: Point[] = []
    for (let d = new Date(de), i = 0; d <= ate && i < 400; d.setDate(d.getDate() + 1), i++) {
        if (d.getDay() === 0 || d.getDay() === 6) continue
        out.push({
            name: d.toISOString().slice(0, 10),
            value: Math.max(0, Math.round(base + base * Math.sin(i * 1.2))),
        })
    }
    return out
}

const comissao = (funcionario: string, taxa: number, qtd: number) => ({
    funcionario,
    taxa_resolvido: taxa,
    taxa_cancelamento: 0,
    qtd_resolvido: qtd,
    valor: 0,
    qtd_x_valor: 0,
    comissao: 0,
})

export function pendenciasLegadoFor(unit: string, query: DashboardQuery): V1GenericoResponse {
    if (unit === 'LA_AM') {
        return {
            meta: metaFor(unit, 'LA'),
            dashboard: 'pendencia_LA',
            stats: {
                pendencias_total_LA: 9,
                pendencias_nao_resolvidas_LA: 8,
                pendencias_nao_resolvidas_com_atraso_LA: 8,
                pendencias_resolvidas_LA: 1,
                pendencias_canceladas_LA: 0,
                pendencias_taxa_resolvidos_LA: 11.11,
                pendencias_taxa_nao_resolvidos_LA: 88.89,
                pendencias_taxa_canceladas_LA: 0,
                pendencias_triagem_LA: 0,
                media_tempo_resolvidos_pendencia_LA: 2,
                mediana_tempo_resolvidos_pendencia_LA: 2,
            },
            pendencias_resolvidas_por_dia_LA: porDia(query, 1),
            pendencias_resolvidas_por_mes_LA: porMes([
                [2024, LA_2024],
                [2025, LA_2025],
                [2026, LA_2026],
            ]),
            pendencias_nao_resolvidas_por_origem_LA: [{ name: 'Sem origem', value: 8 }],
            media_pendencias_resolvidas_por_funcionario_LA: [{ name: 'RENATA APARECIDA', value: 1 }],
            funcionarios_pendencias_LA: ['RENATA APARECIDA'],
            comissionamento_pendencias_LA_por_funcionario: [comissao('RENATA APARECIDA', 11.11, 1)],
        } as V1GenericoResponse
    }
    return {
        meta: metaFor(unit, 'NG'),
        dashboard: unit === 'NG' ? 'pendencias' : 'pendencias_RJ',
        stats: {
            pendencias_total: 2,
            pendencias_nao_resolvidas: 5,
            pendencias_nao_resolvidas_com_atraso: 5,
            pendencias_resolvidas: 0,
            pendencias_canceladas: 0,
            pendencias_taxa_resolvidos: 0,
            pendencias_taxa_nao_resolvidos: 100,
            pendencias_taxa_canceladas: 0,
            pendencias_triagem: 0,
            pendencias_nao_resolvidas_reajuizamento: 0,
            pendencias_resolvidas_reajuizamento: 0,
            media_tempo_resolvidos_pendencia: 0,
            mediana_tempo_resolvidos_pendencia: 0,
            comparativo_pendencias_resolvidas: -100,
            comparativo_tempo_medio_pendencias_resolvidas: 0,
        },
        pendencias_resolvidas_por_dia: porDia(query, 3),
        pendencias_resolvidas_por_mes: porMes([
            [2024, NG_2024],
            [2025, NG_2025],
            [2026, NG_2026],
        ]),
        pendencias_nao_resolvidas_por_origem: [{ name: 'RETORNO COMERCIAL', value: 5 }],
        media_pendencias_resolvidas_por_funcionario: [
            { name: 'JOÃO VICTOR', value: 2.4 },
            { name: 'LETÍCIA ROBERTA', value: 1.6 },
        ],
        funcionarios_pendencias: ['João Victor Mendes', 'LETÍCIA ROBERTA'],
        comissionamento_pendencias_por_funcionario: [comissao('JOÃO VICTOR', 0, 0), comissao('LETÍCIA ROBERTA', 0, 0)],
    } as V1GenericoResponse
}
