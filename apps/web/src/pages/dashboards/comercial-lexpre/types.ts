import type { Meta, Point, WithComparison } from '../../../types/index.ts'

// Uma linha da tabela "Valor das Rubricas" (Comissão Comercial): ações fechadas × VALOR_AM unitário = total.
export type RubricaValor = { rubrica: string; acoes: number; valor_am: number; total: number }

// Resposta do dashboard Comercial (LexPre): os campos da v1 (ComercialLexpreNGResponse) que a tela usa +
// `opcoes_filtro` e `meta_inteligente` (novos na V2). Comparativos em % vs mês anterior.
// V2: a prévia do que ainda pode ser protocolado (dashboards/comercial_lexpre.py, previa_represados): o ticket médio
// protocolado dos últimos 3 meses (de `de` até `ate`, hoje) × os represados agora nos 4 setores do Pré-protocolo.
export type PreviaRepresados = {
    de: string
    ate: string
    ticket_medio: number
    represados: { pendencias: number; org_documentos: number; peticionamento: number; protocolo: number }
    total_represados: number
    valor: number
}

export type ComercialLexpreResponse = {
    meta: Meta
    stats: {
        // Topo · Meta anual: valor de causa protocolado no LexPre no ano corrente (ano_meta), sem o filtro de período.
        valor_causa_protocolado_ano?: number
        ano_meta?: number
        // 01 · Captação: clientes que assinaram contrato no período, por canal de origem.
        clientes_todos: WithComparison
        clientes_campanha: WithComparison
        clientes_redes_sociais: WithComparison
        clientes_retorno: WithComparison
        clientes_resgate: WithComparison
        clientes_indicacao: WithComparison
        clientes_site: WithComparison
        clientes_parceiros: WithComparison
        clientes_externos: WithComparison
        demandas_canceladas: WithComparison
        acoes_fechadas: WithComparison
        rubricas_reunidas_fechadas: number
        taxa_aproveitamento: WithComparison // ações por cliente (razão, não %)
        // 02 · Performance.
        leads_geral: WithComparison
        leads_campanha: WithComparison
        taxa_leads_geral: WithComparison // %
        taxa_leads_campanha: WithComparison // %
        ranking_acoes_fechadas_por_atendente: Point[]
        acoes_fechadas_hoje_por_atendente: Point[]
        contratos_fechados_hoje_por_atendente: Point[]
        // 03 · Protocolos e valor de causa.
        protocolados: WithComparison
        valor_causa_protocolado: WithComparison
        ticket_medio_protocolado: WithComparison
        tempo_medio_ate_protocolo_horas: number
        fila_pre_protocolo_por_atendente: FilaPreProtocolo[]
        valor_causa_por_atendente: { name: string; protocolado: number; nao_protocolado: number; total: number }[]
        // 04 · Rubricas: ações fechadas por rubrica, por canal ('total', 'campanha', 'retorno'...).
        acoes_fechadas_por_rubrica: Record<string, Point[]>
        // 05 · Equipe.
        tabela_por_atendente: LinhaAtendente[]
        totais_tabela_por_atendente: LinhaAtendente
        valor_causa_protocolado_por_atendente_periodo: Record<string, number> // Meta por Atendente
        // Comissão Comercial · 02 Cálculo (a API manda também no Comercial; só a página da Comissão mostra).
        comissao_base?: number
        fator_multiplicador?: number // o "Valor FM" da v1: um fator (ex.: 3,85), não R$
        comissao_com_fm?: number // bruta, antes do desconto
        desconto_cancelamentos?: number
        comissao_com_fm_liquida?: number // o pool que os proporcionais dividem
        proporcional_am_pa?: number
        proporcional_pb?: number
        // Comissão Comercial · 03 "Valor das Rubricas", por canal (mesmas chaves de acoes_fechadas_por_rubrica).
        rubricas_total_tabela?: Record<string, RubricaValor[]>
        // Linhas do PDF "Gerar comissão" (como na v1).
        comissionamento_por_atendente?: {
            atendente: string
            acoes: number
            comissao_base: number
            valor_fm: number
            proporcional_am_pa: number
            proporcional_pb: number
            comissao_com_fm: number
            desconto_cancelamentos: number
        }[]
    }
    // Novo na V2 (o card "Meta Inteligente por Atendente" da v1), por janela de histórico: '3', '6', '12' meses.
    meta_inteligente?: Record<string, MetaInteligente>
    // Novos na V2 (na v1, duas rotas a mais): o protocolado no banco legado da unidade (antes da migração),
    // somado no front. No ano de 2026 (Meta anual) e por atendente no período (Meta por Atendente; chave =
    // primeiro nome, a mesma do LexPre). null = sem legado ligado ou fora do ar.
    valor_causa_protocolado_legado?: number | null
    previa_represados?: PreviaRepresados
    valor_causa_protocolado_por_atendente_legado?: Record<string, number>
    opcoes_filtro: {
        atendentes: string[]
        areas: { id: number; nome: string }[]
        ufs: string[]
        segmentos: string[]
    }
}

// Fila de demandas no pré-protocolo de um atendente (cada etapa, mais o total).
export type FilaPreProtocolo = {
    name: string
    total: number
    pendencias: number
    triagem: number
    nao_organizado: number
    nao_confeccionado: number
    nao_protocolado: number
    protocolado: number
}

// Uma linha do "Detalhamento por Atendente": leads_<canal>, clientes_<canal>, taxa_<canal> (geral e cada canal).
export type LinhaAtendente = { atendente: string } & Record<string, number | string>

export type MetaInteligenteAtendente = {
    atendente: string
    meses_com_dados: number
    historico_mensal: { mes: string; valor: number }[]
    media_simples: number
    media_ponderada: number
    tendencia_mensal: number
    tendencia_label: string // 'crescimento forte' | 'crescimento moderado' | 'estável' | 'queda moderada' | 'queda forte'
    projecao_proximo_mes: number
    meta_sugerida: number
    percentual_da_equipe: number
    meta_proporcional: number
}

export type MetaInteligente = {
    gerado_em: string
    meses_considerados: number
    meta_global: number | null
    atendentes: MetaInteligenteAtendente[]
    totais: { media_equipe_mes?: number; projecao_total_proximo_mes?: number; meta_total_sugerida?: number }
}
