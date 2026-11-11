import type { Meta, WithComparison } from '../../../types/index.ts'

// Resposta do dashboard Peticionamento (LexPre): só os campos que a tela usa.
// Tudo opcional: no modo mock a API devolve `stats: {}` e não manda `opcoes_filtro`.
export type PeticionamentoLexpreResponse = {
    meta: Meta
    stats: {
        // No período (pela data de saída do setor, como na v1).
        total_peticionados?: WithComparison // confeccionados (não cancelados)
        peticionados_manualmente?: WithComparison
        peticionados_automaticamente?: WithComparison // pet_auto
        cancelados?: WithComparison
        protocolados_total?: WithComparison // dos confeccionados, quantos foram protocolados
        valor_causa_confeccionado?: WithComparison
        ticket_medio_confeccionado?: WithComparison
        media_tempo_peticionado?: number // dias
        mediana_tempo_peticionado?: number // dias
        comparativo_tempo_medio_peticionado?: number | null
        comparativo_mediana_tempo_peticionado?: number | null
        // Situação atual do setor (totais, não dependem do período).
        represados?: number
        retorno_org_doc?: number
        retorno_pendencia?: number
        comparativo_retorno_org_doc?: number | null // devoluções no período vs. mês anterior
        comparativo_retorno_pendencia?: number | null
    }
    // Opções dos filtros (as mesmas do Protocolo).
    opcoes_filtro?: {
        materias?: string[]
        funcionarios?: string[]
        ufs?: string[]
        areas?: { id: number; nome: string }[]
    }
}
