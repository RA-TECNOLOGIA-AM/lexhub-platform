import type { ComercialLexpreResponse } from '../comercial-lexpre/types.ts'

// Resposta da Comissão Comercial (LexPre): a mesma do Comercial (a v1 chamava o mesmo endpoint com
// escopo_proprio=true). Quem não gere a unidade recebe a página inteira só com os próprios dados.
export type ComissaoLexpreResponse = ComercialLexpreResponse
