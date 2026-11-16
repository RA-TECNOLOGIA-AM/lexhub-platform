import type { V1GenericoResponse } from '../../pages/dashboards/v1Stats.ts'
import type { DashboardQuery, Point } from '../../types/index.ts'
import { metaFor } from './helpers.ts'

// Peticionamento (banco legado) fictício, na ordem de grandeza das telas da v1: NG (setembro/2026) e LA_RJ no
// formato da rota /peticionamento; LA_AM no da /peticionamento_LA (nomes com _LA, novembro/2026).

const FUNCIONARIOS = ['Millena de', 'Larissa dos', 'Elizabeth Alves', 'Wellington Butel', 'Vitoriamel Morais']
const COMPLETOS = ['Millena de Souza Sá Graça', 'Larissa dos Santos Lisboa', 'Elizabeth Alves']
const PETICIONADOS = [48, 19, 1, 0, 0]
const NAO = [0, 3, 2, 2, 2]
const MEDIA = [4.36, 1.73, 1, 0, 0]
const VALOR = [1_769_055.65, 372_302.27, 15_166.3, 0, 0]
const MATERIAS: [string, number][] = [
    ['RUBRICAS_REUNIDAS', 17],
    ['CESTA', 13],
    ['MORA', 8],
    ['ANP', 7],
    ['INV_FACIL', 4],
    ['RUBRICAS_REUNIDAS_IRDR', 4],
    ['ESPECIFICA', 4],
    ['JUROS_ABUSIVOS', 2],
    ['RMC', 2],
    ['SEGURO', 2],
    ['TIT_CAP', 1],
]
const NAO_MATERIA: [string, number][] = [
    ['RUBRICAS_REUNIDAS', 2],
    ['PARC_CRED_PESS', 2],
    ['SAQUE_TERMINAL', 2],
    ['GASTO_C_CRED', 1],
    ['JUROS_ABUSIVOS', 1],
    ['OP_VENCIDAS', 1],
]
const MES_2024 = [null, null, null, null, 7, 7, 23, 113, 299, 627, 538, 608]
const MES_2025 = [874, 601, 483, 616, 650, 768, 784, 631, 792, 658, 605, 849]
const MES_2026 = [1400, 961, 1356, 835, 710, 608, 557, 418, 380, 412, 120, null]
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
            value: Math.max(0, Math.round((5 + 5 * Math.sin(i * 1.3)) * k)),
        })
    }
    return out
}

export function peticionamentoLegadoFor(unit: string, query: DashboardQuery): V1GenericoResponse {
    if (unit === 'LA_AM') return laFor(unit, query)
    const k = unit === 'NG' ? 1 : 0.4
    const total = Math.round(68 * k)
    const valor = 2_156_524.22 * k
    return {
        meta: metaFor(unit, 'NG'),
        dashboard: unit === 'NG' ? 'peticionamento' : 'peticionamento_RJ',
        stats: {
            total_peticionados: total,
            peticionados_manualmente: Math.round(31 * k),
            peticionados_automaticamente: Math.round(37 * k),
            processos_em_revisao: 5,
            nao_peticionados: 9,
            valor_causa_confeccionado: valor,
            ticket_medio_confeccionado: total ? valor / total : 0,
            resolvidos_reajuizamento_pet: 0,
            nao_resolvidos_reajuizamento: 0,
            media_tempo_peticionado: 23.57,
            mediana_tempo_peticionado: 6,
            comparativo_peticionados: -87.41,
            comparativo_peticionados_manualmente: -81.66,
            comparativo_peticionados_automaticamente: -90.03,
            comparativo_tempo_medio_peticionado: 181.6,
            comparativo_mediana_tempo_pet: 100,
            comparativo_valor_causa_confeccionado: -89.1,
            comparativo_ticket_medio_confeccionado: -13.48,
            comparativo_peticionados_reajuizamento: -100,
            comparativo_nao_peticionados_reajuizamento: -100,
            peticionamento_taxa_resolvidos: 88.31,
            peticionamento_taxa_nao_resolvidos: 11.69,
        },
        peticionados_por_materia: pontos(MATERIAS, k),
        nao_peticionados_por_materia: pontos(NAO_MATERIA),
        peticionados_por_funcionario: porNome(PETICIONADOS.map((v) => Math.round(v * k))),
        nao_peticionados_por_funcionario: porNome(NAO),
        media_peticionado_por_funcionario: porNome(MEDIA),
        valor_peticionado_por_funcionario: porNome(VALOR, k),
        peticionados_por_dia: porDia(query, k),
        peticionados_por_mes: porMes(k),
        nao_peticionados_por_mes: [
            { name: 'out 2025', value: 1 },
            { name: 'jan 2026', value: 1 },
            { name: 'fev 2026', value: 2 },
            { name: 'mar 2026', value: 1 },
            { name: 'jun 2026', value: 1 },
            { name: 'jul 2026', value: 2 },
            { name: 'set 2026', value: 1 },
        ],
        funcionarios_peticionamento: COMPLETOS,
        comissionamento_peticionamento_por_funcionario: [
            {
                funcionario: 'Millena de',
                qtd_acoes_massa: 20,
                valor_acoes_massa: 3,
                qtd_x_valor_massa: 60,
                qtd_acoes_especificas: 1,
                valor_acoes_especificas: 20,
                qtd_x_valor_especificas: 20,
                taxa_resolvidos: 100,
                valor_comissao: 80,
            },
            {
                funcionario: 'Larissa dos',
                qtd_acoes_massa: 6,
                valor_acoes_massa: 1.5,
                qtd_x_valor_massa: 9,
                qtd_acoes_especificas: 3,
                valor_acoes_especificas: 13,
                qtd_x_valor_especificas: 39,
                taxa_resolvidos: 86.36,
                valor_comissao: 48,
            },
        ],
    } as V1GenericoResponse
}

// A rota /peticionamento_LA: os mesmos gráficos com os nomes "confeccionados" e _LA (números da tela da v1).
function laFor(unit: string, query: DashboardQuery): V1GenericoResponse {
    const pessoas = ['JAMINIE FARIAS', 'IASMIM MAYARA', 'ESTHER VITÓRIA', 'VICTORIA CRISTINA']
    return {
        meta: metaFor(unit, 'LA'),
        dashboard: 'peticionamento_LA',
        stats: {
            total_confeccionados_LA: 1,
            confeccionados_manualmente_LA: 1,
            confeccionados_automaticamente_LA: 0,
            nao_confeccionados_LA: 12,
            valor_causa_confeccionado_LA: 28_989.01,
            ticket_medio_confeccionado_LA: 28_989.01,
            tempo_medio_confeccao_LA: 119,
            mediana_tempo_confeccao_LA: 119,
            comparativo_confeccionados_LA: -94.12,
            comparativo_confeccionados_automaticamente_LA: -100,
            comparativo_confeccionados_manualmente_LA: -88.89,
            comparativo_valor_causa_confeccionado_LA: -92.6,
            comparativo_ticket_medio_confeccionado_LA: 25.82,
            comparativo_tempo_medio_confeccionado_LA: 327.75,
            comparativo_mediana_tempo_confeccionado_LA: 417.39,
            peticionamento_taxa_resolvidos_LA: 7.69,
            peticionamento_taxa_nao_resolvidos_LA: 92.31,
            peticionamento_taxa_retorno_protocolo_LA: 50,
            peticionamento_qtd_retorno_protocolo_LA: 1,
            peticionamento_qtd_entrada_protocolo_LA: 2,
        },
        confeccionados_por_materia_LA: [{ name: 'ESPECIFICA', value: 1 }],
        nao_confeccionados_por_materia_LA: pontos([
            ['ESPECIFICA', 4],
            ['REUNIDA_01', 2],
            ['JUROS_ABUSIVOS', 2],
            ['CESTA', 1],
            ['RCC', 1],
            ['SVA', 1],
            ['PROGRESSAO', 1],
        ]),
        confeccionados_por_funcionario_LA: [{ name: pessoas[0], value: 1 }],
        nao_confeccionados_por_funcionario_LA: pessoas.map((name, i) => ({ name, value: [4, 4, 3, 1][i] })),
        media_confeccionado_por_funcionario_LA: [{ name: pessoas[0], value: 1 }],
        valor_confeccionado_por_funcionario_LA: [{ name: pessoas[0], value: 28_989.01 }],
        confeccionados_por_dia_LA: porDia(query, 3),
        confeccionados_por_mes_LA: porMes(0.6),
        nao_confeccionados_por_mes_LA: [
            { name: 'jul 2026', value: 1 },
            { name: 'ago 2026', value: 2 },
            { name: 'set 2026', value: 4 },
            { name: 'nov 2026', value: 5 },
        ],
        funcionarios_confeccao_LA: ['Jaminie Farias dos Santos'],
        comissionamento_peticionamento_LA_por_funcionario: [
            {
                funcionario: pessoas[0],
                qtd_acoes_massa: 0,
                valor_acoes_massa: 0,
                qtd_x_valor_massa: 0,
                qtd_acoes_especificas: 1,
                valor_acoes_especificas: 0,
                qtd_x_valor_especificas: 0,
                taxa_resolvidos: 20,
                valor_comissao: 0,
            },
        ],
    } as V1GenericoResponse
}
