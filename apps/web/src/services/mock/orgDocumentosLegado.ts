import type { V1GenericoResponse } from '../../pages/dashboards/v1Stats.ts'
import type { DashboardQuery, Point } from '../../types/index.ts'
import { metaFor } from './helpers.ts'

// Organização de Documentos (banco legado) fictícia, na ordem de grandeza das telas da v1: NG (setembro/2026)
// e LA_RJ no formato da rota /org-documentos; LA_AM no da /org_doc_LA (nomes com _LA, novembro/2026).

const FUNCIONARIOS = ['Hingrid Conrrado', 'João Pedro', 'José Henrique']
const COMPLETOS = ['Hingrid Conrrado da Silva', 'José Henrique Reis Chagas', 'João Pedro Rodrigues Alves Figueiredo']
const RESOLVIDOS = [21, 16, 9]
const NAO = [3, 8, 0]
const MEDIA = [3.5, 4, 1.8]
const VALOR = [593_651.53, 418_372.28, 340_532.96]
const MATERIAS: [string, number][] = [
    ['RUBRICAS_REUNIDAS', 14],
    ['MORA', 7],
    ['CESTA', 7],
    ['ANP', 5],
    ['-', 3],
    ['ESPECIFICA', 3],
    ['SEGURO', 2],
    ['JUROS_ABUSIVOS', 2],
    ['RUBRICAS_REUNIDAS_IRDR', 2],
    ['PARC_CRED_PESS', 1],
]
const NAO_MATERIA: [string, number][] = [
    ['MORA', 2],
    ['RUBRICAS_REUNIDAS', 1],
    ['JUROS_ABUSIVOS', 1],
    ['AD_DEPOSITANTE', 1],
    ['COBRANCA_IND', 1],
    ['BX_ANT_FIN', 1],
    ['TIT_CAP', 1],
    ['SAQUE_TERMINAL', 1],
    ['INV_FACIL', 1],
    ['PARC_CRED_PESS', 1],
]
const MES_2024 = [null, null, null, null, null, null, 184, 132, 257, 567, 585, 632]
const MES_2025 = [599, 736, 417, 513, 833, 686, 775, 555, 881, 701, 545, 926]
const MES_2026 = [1117, 879, 1779, 856, 716, 566, 638, 467, 412, 380, 95, null]
const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

const pontos = (xs: [string, number][], k = 1): Point[] => xs.map(([name, v]) => ({ name, value: Math.round(v * k) }))
const porNome = (vs: number[], k = 1): Point[] =>
    FUNCIONARIOS.map((name, i) => ({ name, value: vs[i] * k })).filter((p) => p.value > 0)

function porMes(k: number): Point[] {
    const out: Point[] = []
    for (const [ano, vs] of [
        [2024, MES_2024],
        [2025, MES_2025],
        [2026, MES_2026],
    ] as const) {
        vs.forEach((v, i) => v !== null && out.push({ name: `${MESES[i]} ${ano}`, value: Math.round(v * k) }))
    }
    return out
}

function porDia(query: DashboardQuery, k: number): Point[] {
    const de = new Date(`${query.from ?? '2026-10-01'}T12:00:00`)
    const ate = new Date(`${query.to ?? '2026-10-31'}T12:00:00`)
    const out: Point[] = []
    for (let d = new Date(de), i = 0; d <= ate && i < 400; d.setDate(d.getDate() + 1), i++) {
        if (d.getDay() === 0 || d.getDay() === 6) continue
        out.push({
            name: d.toISOString().slice(0, 10),
            value: Math.max(0, Math.round((4 + 4 * Math.sin(i * 1.1)) * k)),
        })
    }
    return out
}

export function orgDocumentosLegadoFor(unit: string, query: DashboardQuery): V1GenericoResponse {
    if (unit === 'LA_AM') return laFor(unit, query)
    const k = unit === 'NG' ? 1 : 0.4
    return {
        meta: metaFor(unit, 'NG'),
        dashboard: unit === 'NG' ? 'org-documentos' : 'org_doc_RJ',
        stats: {
            resolvidos_total: Math.round(46 * k),
            organizados_manualmente: Math.round(25 * k),
            organizados_e_peticionados_automaticamente: Math.round(21 * k),
            resolvidos_reajuizamento: 0,
            cancelados: 0,
            nao_organizados: 11,
            retorno_pendencia: 3,
            retorno_pet: 0,
            media_tempo_resolvidos: 16.43,
            mediana_tempo_resolvidos: 9,
            comparativo_resolvidos_total: -90.06,
            comparativo_organizados_manualmente: -83.33,
            comparativo_organizados_e_peticionados_automaticamente: -93.29,
            comparativo_resolvidos_reajuizamento: 0,
            comparativo_cancelados: 207.1,
            comparativo_tempo_medio_resolvidos_org_doc: 207.1,
        },
        resolvidos_total_por_materia: pontos(MATERIAS, k),
        nao_organizados_total_por_materia: pontos(NAO_MATERIA),
        resolvidos_por_funcionario: porNome(RESOLVIDOS.map((v) => Math.round(v * k))),
        nao_organizados_por_funcionario: porNome(NAO),
        media_resolvidos_por_funcionario: porNome(MEDIA),
        valor_causa_por_funcionario: porNome(VALOR, k),
        resolvidos_por_dia_org: porDia(query, k),
        resolvidos_total_por_mes: porMes(k),
        nao_resolvidos_total_por_mes: [
            { name: 'ago 2026', value: 1 },
            { name: 'set 2026', value: 2 },
            { name: 'out 2026', value: 8 },
        ],
        funcionarios_org_doc: COMPLETOS,
        comissionamento_por_funcionario: FUNCIONARIOS.map((funcionario, i) => ({
            funcionario,
            qtd_resolvidos: Math.round(RESOLVIDOS[i] * k),
            valor_causa_gerado: VALOR[i] * k,
            valor_comissao: [7.48, 4.02, 1.84][i],
        })),
    } as V1GenericoResponse
}

// A rota /org_doc_LA: "organizados" e _LA nos nomes (números da tela da v1).
function laFor(unit: string, query: DashboardQuery): V1GenericoResponse {
    const pessoas = ['ISABELLY CRISTINNE', 'SIRLEIDY CORREA', 'EDUARDA SANTOS', 'IASMIM MAYARA']
    return {
        meta: metaFor(unit, 'LA'),
        dashboard: 'org_doc_LA',
        stats: {
            total_organizados_LA: 10,
            total_organizados_manualmente_LA: 7,
            total_organizados_automaticamente_LA: 3,
            cancelados_LA: 0,
            nao_organizados_LA: 8,
            retorno_pendencia_LA: 35,
            media_tempo_resolvidos_LA: 70.6,
            mediana_tempo_resolvidos_LA: 58,
            comparativo_resolvidos_total_LA: -28.57,
            comparativo_organizados_manualmente_LA: 40,
            comparativo_organizados_automaticamente_LA: -66.67,
            comparativo_cancelados_LA: 0,
        },
        organizados_total_por_materia_LA: pontos([
            ['ESPECIFICA', 3],
            ['JUROS_ABUSIVOS', 2],
            ['PROGRESSAO', 1],
            ['SVA', 1],
            ['REUNIDA_01', 1],
            ['CESTA', 1],
            ['RCC', 1],
        ]),
        nao_organizados_total_por_materia_LA: pontos([
            ['ESPECIFICA', 7],
            ['ATS', 1],
        ]),
        organizados_por_funcionario_LA: pessoas.slice(0, 3).map((name, i) => ({ name, value: [5, 3, 2][i] })),
        nao_organizados_por_funcionario_LA: pessoas.map((name, i) => ({ name, value: [1, 3, 3, 1][i] })),
        media_resolvidos_por_funcionario_LA: pessoas.slice(0, 3).map((name, i) => ({ name, value: [5, 1, 1][i] })),
        valor_causa_por_funcionario_LA: pessoas
            .slice(0, 3)
            .map((name, i) => ({ name, value: [61_811.42, 15_000, 44_049.03][i] })),
        resolvidos_por_dia_LA: porDia(query, 0.6),
        resolvidos_total_por_mes_LA: porMes(0.6),
        nao_organizados_total_por_mes_LA: [
            { name: 'mar 2026', value: 1 },
            { name: 'jun 2026', value: 1 },
            { name: 'jul 2026', value: 1 },
            { name: 'set 2026', value: 5 },
        ],
        funcionarios_org_doc_LA: ['Eduarda Santos Sinarahua', 'ISABELLY CRISTINNE SOUSA', 'Sirleidy Correa da Silva'],
        comissionamento_org_doc_LA_por_funcionario: [
            { funcionario: pessoas[0], qtd_resolvidos: 5, valor_causa_gerado: 61_811.42, valor_comissao: 0.19 },
            { funcionario: pessoas[2], qtd_resolvidos: 2, valor_causa_gerado: 44_049.03, valor_comissao: 0.05 },
            { funcionario: pessoas[1], qtd_resolvidos: 3, valor_causa_gerado: 15_000, valor_comissao: 0.03 },
        ],
    } as V1GenericoResponse
}
