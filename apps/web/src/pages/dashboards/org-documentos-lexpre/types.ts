import type { Meta, WithComparison } from '../../../types/index.ts'

// Ponto de série dos gráficos da v1 (name/value); os demais campos vêm quase sempre null.
export type SeriePonto = { name: string; value: number | null }

// Campos da v1 (OrgDocumentosLexpreNGResponse) + o que é novo da V2 (meta e opcoes_filtro).
// Tudo opcional: no mock vêm só `meta` e `stats: {}`, e a tela precisa funcionar assim.
export type OrgDocumentosLexpreResponse = {
    meta: Meta
    stats?: {
        resolvidos_total?: WithComparison
        organizados_manualmente?: WithComparison
        organizados_e_peticionados_automaticamente?: WithComparison
        cancelados?: WithComparison
        protocolados_total?: WithComparison
        media_tempo_resolvidos?: number | null
        comparativo_tempo_medio_resolvidos?: number | null
        mediana_tempo_resolvidos?: number | null
        comparativo_mediana_tempo_resolvidos?: number | null
        represados?: number | null
        devolvido_pendencia?: number | null
        comparativo_devolvido_pendencia?: number | null
        retorno_pendencia?: number | null
        retorno_pet?: number | null
    }
    // Séries dos gráficos da v1 (ainda não usadas na tela).
    funcionarios_org_doc?: string[]
    resolvidos_total_por_materia?: SeriePonto[]
    nao_organizados_total_por_materia?: SeriePonto[]
    protocolados_total_por_materia?: SeriePonto[]
    resolvidos_por_funcionario?: SeriePonto[]
    media_resolvidos_por_funcionario?: SeriePonto[]
    nao_organizados_por_funcionario?: SeriePonto[]
    protocolados_por_funcionario?: SeriePonto[]
    valor_causa_por_funcionario?: SeriePonto[]
    valor_causa_protocolado_por_funcionario?: SeriePonto[]
    resolvidos_por_dia_org?: SeriePonto[]
    resolvidos_por_dia_por_funcionario_org?: Record<string, SeriePonto[]>
    resolvidos_total_por_mes?: unknown[]
    nao_resolvidos_total_por_mes?: unknown[]
    comissionamento_por_funcionario?: {
        funcionario: string
        qtd_protocolados: number
        valor_causa_protocolado: number
        valor_comissao: number
    }[]
    opcoes_filtro?: {
        materias?: string[]
        funcionarios?: string[]
        ufs?: string[]
        areas?: { id: number; nome: string }[]
    }
}
