import type { Meta, WithComparison } from '../../../types/index.ts'

// Resposta do dashboard Comercial (LexPre): só os campos que a tela usa.
// Tudo opcional: no modo mock a API devolve `stats: {}`.
export type ComercialLexpreResponse = {
    meta: Meta
    stats: {
        // Captação no período (clientes que assinaram contrato, por origem).
        clientes_todos?: WithComparison
        clientes_campanha?: WithComparison
        clientes_indicacao?: WithComparison
        clientes_retorno?: WithComparison
        acoes_fechadas?: WithComparison
        rubricas_reunidas_fechadas?: number
        demandas_canceladas?: WithComparison
        taxa_aproveitamento?: WithComparison // ações por cliente (razão, não %)
        // Leads do período.
        leads_geral?: WithComparison
        taxa_leads_geral?: WithComparison // %
        leads_campanha?: WithComparison
        taxa_leads_campanha?: WithComparison // %
        // Protocolo no período.
        protocolados?: WithComparison
        valor_causa_protocolado?: WithComparison
        ticket_medio_protocolado?: WithComparison
        tempo_medio_ate_protocolo_horas?: number
    }
}
