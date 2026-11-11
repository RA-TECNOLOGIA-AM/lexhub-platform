import type { Meta, WithComparison } from '../../../types/index.ts'

// Uma linha da tabela "Comissão por atendente" (valores em R$, exceto ações e FM).
export type ComissaoAtendente = {
    atendente: string
    acoes?: number
    comissao_base?: number
    comissao_com_fm?: number
    desconto_cancelamentos?: number
    proporcional_am_pa?: number
    proporcional_pb?: number
}

// Resposta do dashboard Comissão Comercial (LexPre): só os campos que a tela usa.
// Mesmo cálculo do Comercial LexPre; quem não gere a unidade recebe só os próprios dados.
// Tudo opcional: no modo mock a API devolve `stats: {}`.
export type ComissaoLexpreResponse = {
    meta: Meta
    stats: {
        // Cálculo da comissão (pool do período).
        comissao_base?: number
        fator_multiplicador?: number
        comissao_com_fm?: number // bruta, antes do desconto
        desconto_cancelamentos?: number
        comissao_com_fm_liquida?: number
        // Divisão do pool líquido por estado.
        proporcional_am_pa?: number
        proporcional_pb?: number
        // Base do período.
        acoes_fechadas?: WithComparison
        rubricas_reunidas_fechadas?: number
        protocolados?: WithComparison
        valor_causa_protocolado?: WithComparison
        demandas_canceladas?: WithComparison
        // Detalhe por atendente.
        comissionamento_por_atendente?: ComissaoAtendente[]
    }
}
