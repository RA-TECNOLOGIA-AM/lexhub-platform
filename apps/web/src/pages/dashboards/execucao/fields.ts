// Mapa dos campos de `stats` do dashboard Execução, por unidade.
//
// Na v1 cada unidade tinha sua rota e sua página (NG/Execucao.tsx, LA/Execucao_LA.tsx,
// RJ/ExecucaoRJ.tsx), e o backend devolve nomes diferentes para cada uma:
// - NG: indicadores SEM sufixo (total_em_execucao, tre...), mas atividades e diligências com `_NG`;
// - LA e RJ: sufixo `_LA` / `_RJ` em todos os campos.
// Conferido nas respostas reais da v1 (mês anterior) das três unidades.
// `null` = a unidade não tem esse indicador (a tela mostra '—').

export type Unidade = 'NG' | 'LA' | 'RJ'

export type CampoExecucao =
    // No período (pela data de entrada / de compensação do alvará)
    | 'entradas' // "Quantidade de entrada na Execução"
    | 'valorEntradas' // "Valor em Execução" (valor da execução dos que entraram)
    | 'saidas' // "Quantidade de saída da Execução"
    | 'saidasIncontroverso' // "Qtd. Incontroverso"
    | 'valorSaidas' // "Valor Total saída Execução"
    | 'valorTedSaidas' // "Valor TED"
    | 'valorIncontroverso' // "Valor Incontroverso"
    | 'taxaRecuperacao' // "Taxa de Recuperação" (%) — na v1 estava comentada ("em espera")
    // Tempo e estoque
    | 'mediaTempo' // "Média de Tempo" (dias)
    | 'medianaTempo' // "Mediana de tempo" (dias)
    | 'estoqueInicial' // "Estoque Inicial do período anterior"
    | 'tre' // "Taxa de Redução Estoque (TRE)" (razão, 2 casas)
    // Valores dos processos em execução
    | 'valorTotal' // "Valor Total em execução"
    | 'valorRemanescente' // "Valor Remanescente"
    | 'honorarios' // honorários (não aparecia como card na v1)
    // Atividades e prazos
    | 'atividadesTotal' // "Total de atividades"
    | 'atividadesConcluidas' // "Concluídas"
    | 'atividadesVencidas' // "Vencidas"
    | 'atividadesVencemHoje' // "Vencem hoje"
    | 'alvarasCumpridos' // "Expedições de Alvará Cumpridas" (seção Diligências)

export const CAMPOS: Record<Unidade, Record<CampoExecucao, string | null>> = {
    NG: {
        entradas: 'total_em_execucao',
        valorEntradas: 'valor_em_execucao',
        saidas: 'total_saida_execucao_periodo',
        saidasIncontroverso: 'total_incontroverso_saida_execucao_periodo',
        valorSaidas: 'valor_execucao_saida_periodo',
        valorTedSaidas: 'valor_ted_saida_execucao_periodo',
        valorIncontroverso: 'valor_incontroverso_saida_execucao_periodo',
        taxaRecuperacao: 'taxa_recuperacao_execucao',
        mediaTempo: 'media_tempo_execucao',
        medianaTempo: 'mediana_tempo_execucao',
        estoqueInicial: 'estoque_inicial',
        tre: 'tre',
        valorTotal: 'valor_total_em_execucao',
        valorRemanescente: 'valor_remanescente_em_execucao',
        honorarios: 'valor_honorarios_total_execucao',
        atividadesTotal: 'total_atividades_execucao_NG',
        atividadesConcluidas: 'atividades_execucao_concluidas_NG',
        atividadesVencidas: 'atividades_execucao_vencidas_NG',
        atividadesVencemHoje: 'atividades_execucao_vencem_hoje_NG',
        alvarasCumpridos: 'cumpridas_diligencias_expedicao_alvara_execucao_NG',
    },
    LA: {
        entradas: 'total_em_execucao_LA',
        valorEntradas: 'valor_em_execucao_LA',
        saidas: 'total_saida_execucao_periodo_LA',
        saidasIncontroverso: 'total_incontroverso_saida_execucao_periodo_LA',
        valorSaidas: 'valor_execucao_saida_periodo_LA',
        valorTedSaidas: 'valor_ted_saida_execucao_periodo_LA',
        valorIncontroverso: 'valor_incontroverso_saida_execucao_periodo_LA',
        taxaRecuperacao: 'taxa_recuperacao_execucao_LA',
        mediaTempo: 'media_tempo_execucao_LA',
        medianaTempo: 'mediana_tempo_execucao_LA',
        estoqueInicial: 'estoque_inicial_LA',
        tre: 'tre_LA',
        valorTotal: 'valor_total_em_execucao_LA',
        valorRemanescente: 'valor_remanescente_em_execucao_LA',
        honorarios: 'valor_honorarios_total_execucao_LA',
        atividadesTotal: 'total_atividades_execucao_LA',
        atividadesConcluidas: 'atividades_execucao_concluidas_LA',
        atividadesVencidas: 'atividades_execucao_vencidas_LA',
        atividadesVencemHoje: 'atividades_execucao_vencem_hoje_LA',
        alvarasCumpridos: null, // a página da v1 do LA não tem a seção Diligências; a API não devolve
    },
    RJ: {
        entradas: 'total_em_execucao_RJ',
        valorEntradas: 'valor_em_execucao_RJ',
        saidas: 'total_saida_execucao_periodo_RJ',
        saidasIncontroverso: 'total_incontroverso_saida_execucao_periodo_RJ',
        valorSaidas: 'valor_execucao_saida_periodo_RJ',
        valorTedSaidas: 'valor_ted_saida_execucao_periodo_RJ',
        valorIncontroverso: 'valor_incontroverso_saida_execucao_periodo_RJ',
        taxaRecuperacao: 'taxa_recuperacao_execucao_RJ',
        mediaTempo: 'media_tempo_execucao_RJ',
        medianaTempo: 'mediana_tempo_execucao_RJ',
        estoqueInicial: 'estoque_inicial_RJ',
        tre: 'tre_RJ',
        valorTotal: 'valor_total_em_execucao_RJ',
        valorRemanescente: 'valor_remanescente_em_execucao_RJ',
        honorarios: 'valor_honorarios_total_execucao_RJ',
        atividadesTotal: 'total_atividades_execucao_RJ',
        atividadesConcluidas: 'atividades_execucao_concluidas_RJ',
        atividadesVencidas: 'atividades_execucao_vencidas_RJ',
        atividadesVencemHoje: 'atividades_execucao_vencem_hoje_RJ',
        alvarasCumpridos: 'cumpridas_diligencias_expedicao_alvara_execucao_RJ',
    },
}

function isUnidade(unit: string): unit is Unidade {
    return unit === 'NG' || unit === 'LA' || unit === 'RJ'
}

// Nome do campo em `stats` para a unidade; null se a unidade (ou o indicador) não existe.
export function nomeCampo(chave: CampoExecucao, unit: string): string | null {
    return isUnidade(unit) ? CAMPOS[unit][chave] : null
}

// Valor numérico do indicador; null quando falta (campo ausente, null ou não numérico).
export function campo(stats: Record<string, unknown> | undefined, chave: CampoExecucao, unit: string): number | null {
    const nome = nomeCampo(chave, unit)
    if (!stats || !nome) return null
    const v = stats[nome]
    return typeof v === 'number' && Number.isFinite(v) ? v : null
}

// Divisão para tickets médios (valor / quantidade); null se faltar algum lado ou a quantidade for 0.
export function razao(valor: number | null, quantidade: number | null): number | null {
    return valor === null || quantidade === null || quantidade === 0 ? null : valor / quantidade
}
