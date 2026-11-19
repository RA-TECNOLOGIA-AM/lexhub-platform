import type { Meta } from '../../../types/index.ts'

// Resposta de GET .../dashboards/financeiro-estrategico: as quatro rotas da v1 (financeiro_estrategico_<NG|LA>,
// /conversao, /previsao e /clientes_pendentes) numa resposta só, com os mesmos campos.

export type Comparado = { valor: number; valor_anterior: number; comparativo: number | null }
export type Fatia = { name: string; value: number; quantidade?: number } // pizzas (value = R$)
export type OrigemFatia = { name: string; quantidade: number; valor: number; percentual: number }
export type MesHistorico = { ano: number; mes: number; entradas: number; receita: number; ticket_medio: number }
export type ReflexoMes = { ano: number | null; mes: number | null; entradas: number; receita: number }
export type Mediana = {
    dias: number
    dias_anterior: number
    meses: number
    meses_anterior: number
    comparativo: number | null
}

export type ValorProtocolado = Comparado & { quantidade: number; quantidade_anterior: number; por_materia: Fatia[] }

export type ReflexoAjuizamento = {
    periodo: { inicio: string; fim: string } // o período próprio da seção (aj_de/aj_ate; padrão: este ano)
    valor_protocolado: ValorProtocolado // LexFlow, no período da seção
    total_entradas: Comparado
    valor_receita: Comparado
    ticket_medio: Comparado
    mediana_tempo_ajuizamento_ted: Mediana
    receita_por_materia: Fatia[]
    origem: OrigemFatia[]
    receita_por_ano_ted: Fatia[]
    reflexo_do_mes_ted: ReflexoMes[]
    percentual_procedentes: Comparado
}

export type ReflexoFinanceiro = {
    periodo: { inicio: string; fim: string; inicio_anterior: string; fim_anterior: string }
    total_entradas: Comparado
    valor_receita: Comparado
    ticket_medio: Comparado
    clientes_pendentes: { valor: number; quantidade: number }
    causa_x_receita: { valor_causa: number; valor_receita: number }
    origem: OrigemFatia[]
    receita_por_materia: Fatia[]
    receita_por_ano_ajuizamento: Fatia[]
    historico_mensal: MesHistorico[]
    evolucao_anual: { ano: number; receita: number; crescimento_pct: number | null }[]
    reflexo_do_mes: ReflexoMes[]
    filtros_opcoes: { origens: string[]; materias: string[]; anos_ajuizamento: string[] }
    reflexo_ajuizamento: ReflexoAjuizamento
    mediana_tempo_ajuizamento_ted: Mediana
    // LexFlow: valor de causa dos processos distribuídos no período (não muda com os filtros da planilha)
    valor_protocolado: ValorProtocolado
}

export type Conversao = {
    receita: number
    quantidade: number
    valor_causa_ajuizado: { valor: number; quantidade: number }
    percentual_conversao: number
    receita_por_materia: Fatia[]
    receita_por_ano_ajuizamento: Fatia[]
    anos_ajuizamento_opcoes: string[]
    anos_financeiro_opcoes: string[]
}

export type Cenario = {
    id: string
    nome: string
    rotulo: string // 'Base' | 'Conservador' | 'Otimista' | 'Intermediário'
    valor: number
    crescimento_pct: number | null
    premissa: string
    explicacao: string
    quando_faz_sentido: string
    detalhe: string
}

export type Previsao = {
    data_referencia: string
    ano_atual: number
    ano_previsto: number
    receita_anual_real: { ano: number; receita: number }[]
    ano_atual_ate_hoje: number
    ano_atual_estimado: number
    fracao_restante_pct: number
    anos_referencia_fracao: number[]
    cenarios: Cenario[]
    cenario_base: string | null
    faixa: { minimo: number; maximo: number } | null
    conferencia_safra: { ano: number; previsto: number; real: number; erro_pct: number } | null
    taxas_safra_pct: Record<string, number>
    aviso_historico: string | null
}

export type ClientesPendentes = {
    valor_fixo: number // a foto inteira (= card), sem ano/mês
    valor_variavel: number // com o ano e o mês do TED escolhidos
    quantidade: number
    quantidade_clientes: number
    por_status: Fatia[]
    por_cliente: Fatia[]
    anos_opcoes: string[]
}

export type FinanceiroEstrategicoResponse = {
    meta: Meta
    escritorio?: 'NG' | 'LA'
    reflexo_financeiro?: ReflexoFinanceiro
    conversao?: Conversao
    previsao?: Previsao
    clientes_pendentes?: ClientesPendentes
}
