// Mapa dos KPIs de Acordos para os campos da resposta, por unidade.
//
// De onde vêm os nomes: páginas da v1 NG/ExecucaoAcordos.tsx, LA/ExecucaoAcordosLA.tsx e
// RJ/ExecucaoAcordosRJ.tsx (rotas /execucao_acordos_NG, _LA, _RJ), conferidos nas respostas
// reais das três unidades (11/11). Nas três o nome é o mesmo nome-base + `_<UNIDADE>`;
// se alguma unidade divergir, a exceção entra em EXCECOES sem mexer na tela.

export const UNIDADES_ACORDOS = ['NG', 'LA', 'RJ'] as const
export type UnidadeAcordos = (typeof UNIDADES_ACORDOS)[number]

// Nome-base de cada KPI (sem o sufixo da unidade) e o rótulo/cartão da v1 que o usa.
const BASE = {
    // "Indicadores" (independem do período na v1: vêm da consulta sem filtro de data).
    totalEmExecucao: 'total_em_execucao_acordos', // Total em Execução de Acordos
    valorTotalEmExecucao: 'valor_total_em_execucao_acordos', // Valor Total em Execução de Acordos
    // "Indicadores" (no período).
    entradas: 'total_entrada_execucao_acordos_periodo', // Entradas de Acordos
    valorEntradas: 'valor_entrada_execucao_acordos_periodo', // Valor de Entradas de Acordos
    pagos: 'total_saida_execucao_acordos_periodo', // Acordos Pagos no Período
    valorPagos: 'valor_saida_execucao_acordos_periodo', // Valor de Acordos Pagos
    mediaTempo: 'media_tempo_execucao_acordos', // Média de Tempo (dias)
    medianaTempo: 'mediana_tempo_execucao_acordos', // Mediana de Tempo (dias)
    estoqueInicial: 'estoque_inicial_execucao_acordos', // Estoque Inicial do período anterior
    tre: 'tre_execucao_acordos', // Taxa de Redução Estoque (TRE), em %
    // "Atividades no período" (visão "criadas no período" da v1).
    atividadesTotal: 'total_atividades_execucao_acordos', // Total de atividades
    atividadesEmAndamento: 'atividades_execucao_em_andamento_acordos', // Em andamento
    atividadesVencidas: 'atividades_execucao_vencidas_acordos', // Vencidas
    atividadesVencemHoje: 'atividades_execucao_vencem_hoje_acordos', // Vencem hoje
    atividadesConcluidas: 'atividades_execucao_concluidas_acordos', // Concluídas
    // "Diligências".
    diligenciasTotal: 'total_diligencias_execucao_acordos', // N diligência(s) no período
    alvaraDiligencias: 'total_diligencias_expedicao_alvara_execucao_acordos', // Diligências de Expedição de Alvará
    alvaraCumpridas: 'cumpridas_diligencias_expedicao_alvara_execucao_acordos', // Expedições de Alvará Cumpridas
    alvaraValorRealizado: 'valor_diligencias_expedicao_alvara_execucao_acordos', // Valor Realizado (Alvará)
} as const

export type AcordosKpi = keyof typeof BASE
export const ACORDOS_KPIS = Object.keys(BASE) as AcordosKpi[]

// Exceções por unidade: nome diferente, ou null quando o KPI não existe na unidade (tela mostra '—').
// Hoje nenhuma: as três unidades usam o mesmo nome-base.
const EXCECOES: Partial<Record<UnidadeAcordos, Partial<Record<AcordosKpi, string | null>>>> = {}

function isUnidade(unit: string): unit is UnidadeAcordos {
    return (UNIDADES_ACORDOS as readonly string[]).includes(unit)
}

// Nome do campo de cada KPI na unidade; unidade desconhecida = tudo null.
export function camposAcordos(unit: string): Record<AcordosKpi, string | null> {
    const campos = {} as Record<AcordosKpi, string | null>
    for (const kpi of ACORDOS_KPIS) {
        if (!isUnidade(unit)) {
            campos[kpi] = null
            continue
        }
        const excecao = EXCECOES[unit]?.[kpi]
        campos[kpi] = excecao !== undefined ? excecao : `${BASE[kpi]}_${unit}`
    }
    return campos
}

// Valores dos KPIs da unidade; o que faltar (ou não for número) fica undefined.
export function lerAcordos(stats: Record<string, unknown>, unit: string): Record<AcordosKpi, number | undefined> {
    const campos = camposAcordos(unit)
    const valores = {} as Record<AcordosKpi, number | undefined>
    for (const kpi of ACORDOS_KPIS) {
        const campo = campos[kpi]
        const v = campo === null ? undefined : stats[campo]
        valores[kpi] = typeof v === 'number' ? v : undefined
    }
    return valores
}
