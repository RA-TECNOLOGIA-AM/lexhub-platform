import type { RecursalStats } from './types.ts'

// Mapa KPI → nome do campo em `stats`, por unidade.
// Fonte: respostas reais da v1 (/recursal_NG e /recursal_LA, mês anterior) e as páginas da v1
// (LexHub: pages/dashboards/NG/Recursal.tsx, LA/Recursal_LA.tsx, components/dashboard/
// RecursalDecisaoKpiCards.tsx e RecursalAtividadeKpiCards.tsx).
// Nas duas unidades o nome é o mesmo com o sufixo _NG ou _LA; o que só existe em uma unidade
// fica null na outra (a tela mostra '—').

export type RecursalUnit = 'NG' | 'LA'

export type RecursalKpi =
    // Estoque e entradas
    | 'estoque' // total_recursal_X: processos na fase recursal (ID_FASE = 8), sem filtro de data
    | 'entradas' // entrada_recursal_X: fase 8 com DT_ENTRADA_RECURSAL no período
    | 'valorEntradaAcordao' // valor_causa_acordo_recursal_X: "Valor entrada acórdão Recursal"
    // Status 1º grau (sentenças) e 2º grau (acórdãos) no período
    | 'sentencaFavoravel' // total_sentenca_favoravel_recurso_X
    | 'sentencaParcialFavoravel' // total_sentenca_parcialmente_favoravel_recurso_X
    | 'sentencaDesfavoravel' // total_sentenca_desfavoravel_recurso_X (improcedentes)
    | 'sentencaExtincao' // total_sentenca_extincao_recurso_X (extinto sem mérito)
    | 'acordaoFavoravel' // total_acordao_favoravel_recurso_X
    | 'acordaoParcialFavoravel' // total_acordao_parcialmente_favoravel_recurso_X
    | 'acordaoDesfavoravel' // total_acordao_desfavoravel_recurso_X (improcedentes)
    | 'acordaoExtincao' // total_acordao_extincao_recurso_X (extinto sem mérito)
    // Decisões (RecursalDecisaoKpiCards da v1): quantidade e % do total de decisões
    | 'decisoes' // total_decisoes_recursal_X
    | 'mantidoGanho' // total_mantido_ganho_recurso_X
    | 'mantidoGanhoPct' // percent_mantido_ganho_recursal_X
    | 'revertidoGanho' // total_revertido_ganho_recurso_X
    | 'revertidoGanhoPct' // percent_revertido_ganho_recursal_X
    | 'mantidoPerda' // total_mantido_perda_recurso_X
    | 'mantidoPerdaPct' // percent_mantido_perda_recursal_X
    // Atividades criadas no período (RecursalAtividadeKpiCards da v1, visão padrão, não "por prazo")
    | 'atividades' // total_atividades_recursos_X
    | 'atividadesEmAndamento' // atividades_recursos_em_andamento_X
    | 'atividadesVencidas' // atividades_recursos_vencidas_X
    | 'atividadesVencemHoje' // atividades_recursos_vencem_hoje_X
    | 'atividadesConcluidas' // atividades_recursos_concluidas_X
    // Meta de provimento mensal: só NG na v1 (a página LA não tem esse bloco)
    | 'provimentoQtd' // provimento_mensal_qtd_NG
    | 'provimentoMeta' // provimento_mensal_meta_NG (a v1 usa 80 quando falta; aqui mostra '—')

// Nome-base de cada KPI; o sufixo da unidade é acrescentado em recursalFields().
const BASE: Record<RecursalKpi, string> = {
    estoque: 'total_recursal',
    entradas: 'entrada_recursal',
    valorEntradaAcordao: 'valor_causa_acordo_recursal',
    sentencaFavoravel: 'total_sentenca_favoravel_recurso',
    sentencaParcialFavoravel: 'total_sentenca_parcialmente_favoravel_recurso',
    sentencaDesfavoravel: 'total_sentenca_desfavoravel_recurso',
    sentencaExtincao: 'total_sentenca_extincao_recurso',
    acordaoFavoravel: 'total_acordao_favoravel_recurso',
    acordaoParcialFavoravel: 'total_acordao_parcialmente_favoravel_recurso',
    acordaoDesfavoravel: 'total_acordao_desfavoravel_recurso',
    acordaoExtincao: 'total_acordao_extincao_recurso',
    decisoes: 'total_decisoes_recursal',
    mantidoGanho: 'total_mantido_ganho_recurso',
    mantidoGanhoPct: 'percent_mantido_ganho_recursal',
    revertidoGanho: 'total_revertido_ganho_recurso',
    revertidoGanhoPct: 'percent_revertido_ganho_recursal',
    mantidoPerda: 'total_mantido_perda_recurso',
    mantidoPerdaPct: 'percent_mantido_perda_recursal',
    atividades: 'total_atividades_recursos',
    atividadesEmAndamento: 'atividades_recursos_em_andamento',
    atividadesVencidas: 'atividades_recursos_vencidas',
    atividadesVencemHoje: 'atividades_recursos_vencem_hoje',
    atividadesConcluidas: 'atividades_recursos_concluidas',
    provimentoQtd: 'provimento_mensal_qtd',
    provimentoMeta: 'provimento_mensal_meta',
}

// KPIs que não existem numa unidade (conferido nas respostas reais da v1).
const MISSING: Record<RecursalUnit, readonly RecursalKpi[]> = {
    NG: [],
    LA: ['provimentoQtd', 'provimentoMeta'],
}

export const RECURSAL_KPIS = Object.keys(BASE) as RecursalKpi[]

export function isRecursalUnit(unit: string): unit is RecursalUnit {
    return unit === 'NG' || unit === 'LA'
}

// Nome do campo de cada KPI na unidade; null = não existe nessa unidade (ou unidade desconhecida).
export function recursalFields(unit: string): Record<RecursalKpi, string | null> {
    const fields = {} as Record<RecursalKpi, string | null>
    for (const kpi of RECURSAL_KPIS) {
        fields[kpi] = isRecursalUnit(unit) && !MISSING[unit].includes(kpi) ? `${BASE[kpi]}_${unit}` : null
    }
    return fields
}

// Valores dos KPIs já lidos de `stats`; ausente/null vira null (a tela mostra '—').
export function pickRecursal(stats: RecursalStats | undefined, unit: string): Record<RecursalKpi, number | null> {
    const fields = recursalFields(unit)
    const values = {} as Record<RecursalKpi, number | null>
    for (const kpi of RECURSAL_KPIS) {
        const field = fields[kpi]
        const v = field && stats ? stats[field] : null
        values[kpi] = typeof v === 'number' ? v : null
    }
    return values
}
