import type { V1GenericoResponse } from '../../pages/dashboards/v1Stats.ts'
import type { DashboardQuery, Point } from '../../types/index.ts'
import { metaFor } from './helpers.ts'

// Protocolo (banco legado) fictício, na ordem de grandeza das telas da v1. NG e LA_RJ vêm no formato da rota
// /protocolo (banco NG); LA_AM, no da /protocolo_LA (nomes com _LA), para a tela ler os dois.

const FUNCIONARIOS = [
    'MATEUS ALEXANDRE',
    'SANDRA HELENA',
    'JOSE HENRIQUE',
    'EMERSON SOARES',
    'JOAO PEDRO',
    'HINGRID CONRRADO',
    'MILLENA DE',
    'LARISSA DOS',
]
const PROTOCOLADOS = [3951, 1687, 983, 278, 158, 41, 8, 2]
const NAO = [2, 0, 0, 0, 0, 0, 2, 2]
const MEDIA = [27.63, 21.91, 32.77, 25.27, 31.6, 6.83, 2.1, 1.33]
const VALOR = [115_080_507.9, 40_628_406.47, 26_679_329.05, 9_821_896.89, 3_083_025.64, 993_661.52, 41_220.1, 31_511.93]
const MATERIAS: [string, number][] = [
    ['ANP', 1480],
    ['CESTA', 902],
    ['PARC_CRED_PESS', 811],
    ['SEGURO', 655],
    ['MORA', 540],
    ['JUROS_ABUSIVOS', 498],
    ['EMISSAO_EXTRATO', 377],
    ['SAQUE_TERMINAL', 341],
    ['TIT_CAP', 302],
    ['GASTO_C_CRED', 266],
    ['ENCARGOS_LIMITE_CRED', 231],
    ['INV_FACIL', 190],
    ['BX_ANT_FIN', 150],
    ['COBRANCA_IND', 120],
    ['RUBRICAS_REUNIDAS_IRDR', 90],
    ['Sem matéria', 50],
]
const NAO_MATERIA: [string, number][] = [
    ['JUROS_ABUSIVOS', 2],
    ['MORA', 2],
    ['RUBRICAS_REUNIDAS_IRDR', 1],
    ['INV_FACIL', 1],
    ['ANP', 1],
    ['COBRANCA_IND', 1],
    ['TIT_CAP', 1],
    ['BX_ANT_FIN', 1],
    ['SAQUE_TERMINAL', 1],
    ['EMISSAO_EXTRATO', 1],
]
const SISTEMAS: [string, number][] = [
    ['PJE', 6420],
    ['PROJUDI', 310],
    ['ESAJ', 190],
    ['EPROC', 120],
    ['TJ-AM', 62],
]
const MES_2024 = [null, null, null, null, null, null, 81, 217, 267, 498, 575, 179]
const MES_2025 = [545, 401, 677, 520, 1139, 1069, 782, 535, 867, 615, 562, 961]
const MES_2026 = [983, 911, 1492, 1097, 613, 579, 842, 478, 412, 508, 180, null]
const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

const pontos = (xs: [string, number][], k = 1): Point[] => xs.map(([name, v]) => ({ name, value: Math.round(v * k) }))
const porNome = (vs: number[], k = 1): Point[] => FUNCIONARIOS.map((name, i) => ({ name, value: vs[i] * k }))

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

// Dias úteis do período pedido (ou de outubro/2026), com uma série que sobe e desce como a da v1.
function porDia(query: DashboardQuery, k: number): Point[] {
    const de = new Date(`${query.from ?? '2026-10-01'}T12:00:00`)
    const ate = new Date(`${query.to ?? '2026-10-31'}T12:00:00`)
    const out: Point[] = []
    for (let d = new Date(de), i = 0; d <= ate && i < 400; d.setDate(d.getDate() + 1), i++) {
        if (d.getDay() === 0 || d.getDay() === 6) continue
        const v = Math.max(0, Math.round((40 + 32 * Math.sin(i * 0.9) + (i % 7) * 6) * k))
        out.push({ name: d.toISOString().slice(0, 10), value: v })
    }
    return out
}

export function protocoloLegadoFor(unit: string, query: DashboardQuery): V1GenericoResponse {
    const la = unit === 'LA_AM'
    const k = unit === 'NG' ? 1 : unit === 'LA_AM' ? 0.42 : 0.18
    const sel = query.filters?.funcionario ?? []
    const f = (i: number) => (sel.length === 0 || sel.includes(FUNCIONARIOS[i]) ? 1 : 0)
    const protocolados = Math.round(PROTOCOLADOS.reduce((s, v, i) => s + v * f(i), 0) * k)
    const valor = VALOR.reduce((s, v, i) => s + v * f(i), 0) * k
    const represados = 12
    const comissao = FUNCIONARIOS.map((funcionario, i) => ({
        funcionario,
        qtd_protocolados: Math.round(PROTOCOLADOS[i] * k),
        comissao_unitaria: 1.5,
        valor_comissao: Math.round(PROTOCOLADOS[i] * k) * 1.5,
    }))
    const listas = {
        porMateria: pontos(MATERIAS, k),
        naoPorMateria: pontos(NAO_MATERIA),
        porFuncionario: porNome(PROTOCOLADOS.map((v) => Math.round(v * k))),
        naoPorFuncionario: porNome(NAO),
        media: porNome(MEDIA),
        valor: porNome(VALOR, k),
        sistema: pontos(SISTEMAS, k),
        dia: porDia(query, k),
        mes: porMes(k),
        naoMes: [
            { name: 'mai 2026', value: 6 },
            { name: 'jul 2026', value: 2 },
            { name: 'ago 2026', value: 2 },
            { name: 'set 2026', value: 2 },
        ],
    }

    if (la) {
        return {
            meta: metaFor(unit, 'LA'),
            dashboard: 'protocolo_LA',
            stats: {
                protocolos_resolvidos_LA: protocolados,
                protocolos_represados_LA: represados,
                valor_causa_protocolado_LA: valor,
                ticket_medio_protocolos_resolvidos_LA: protocolados ? valor / protocolados : 0,
                media_tempo_protocolo_LA: 7.46,
                mediana_tempo_protocolo_LA: 4,
                comparativo_protocolos_resolvidos_LA: -11.89,
                comparativo_valor_causa_protocolado_LA: -8.73,
                comparativo_ticket_medio_protocolos_resolvidos_LA: 3.6,
                comparativo_tempo_medio_protocolos_resolvidos_LA: 4.18,
                comparativo_mediana_tempo_protocolos_resolvidos_LA: -2.5,
                taxa_protocolados_LA: 91.4,
                entradas_protocolo_LA: Math.round(protocolados / 0.914),
            },
            protocolados_por_materia_LA: listas.porMateria,
            represados_protocolo_por_materia_LA: listas.naoPorMateria,
            protocololados_por_funcionario_LA: listas.porFuncionario,
            represados_protocolo_por_funcionario_LA: listas.naoPorFuncionario,
            media_protocolados_por_funcionario_LA: listas.media,
            valor_causa_protocolo_por_funcionario_LA: listas.valor,
            protocolados_por_sistema_LA: listas.sistema,
            protocolados_por_dia_LA: listas.dia,
            protocolados_por_mes_LA: listas.mes,
            represados_por_mes_LA: listas.naoMes,
            funcionarios_protocolo_LA: FUNCIONARIOS,
            comissionamento_protocolo_LA_por_funcionario: comissao,
        } as V1GenericoResponse
    }

    return {
        meta: metaFor(unit, 'NG'),
        dashboard: unit === 'NG' ? 'protocolo' : 'protocolo_RJ',
        stats: {
            protocolos_resolvidos: protocolados,
            nao_protocolados: represados,
            protocolados_de_reajuizamento: Math.round(81 * k),
            nao_protocolados_de_reajuizamento: 0,
            valor_causa_protocolo_novo: valor,
            ticket_medio_protocolos_resolvidos: protocolados ? valor / protocolados : 0,
            media_tempo_protocolado: 7.46,
            mediana_tempo_protocolado: 4,
            comparativo_protocolos_resolvidos: -11.89,
            comparativo_valor_causa_protocolo: -8.73,
            comparativo_tempo_medio_protocolos_resolvidos: 4.18,
        },
        protocolados_por_materia: listas.porMateria,
        nao_protocolados_por_materia: listas.naoPorMateria,
        protocolados_por_funcionario: listas.porFuncionario,
        nao_protocolados_por_funcionario: listas.naoPorFuncionario,
        media_protocolados_por_funcionario: listas.media,
        valor_causa_protocolo_novo_por_funcionario: listas.valor,
        protocolados_por_sistema: listas.sistema,
        protocolados_por_dia: listas.dia,
        protocolados_por_mes: listas.mes,
        nao_protocolados_por_mes: listas.naoMes,
        funcionarios_protocolo: FUNCIONARIOS,
        comissionamento_protocolo_por_funcionario: comissao,
    } as V1GenericoResponse
}
