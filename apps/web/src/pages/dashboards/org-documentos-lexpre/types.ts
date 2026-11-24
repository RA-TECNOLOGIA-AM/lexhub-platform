import type { Meta, Point, WithComparison } from '../../../types/index.ts'
import type { RubricaReunida } from '../setor/rubricas.ts'

// Resposta do dashboard Organização de documentos (LexPre): os campos da v1 (OrgDocLexpreNGResponse) que a
// tela usa + `opcoes_filtro` (novo na V2). Tempos em dias; comparativos em % vs mês anterior.
export type OrgDocumentosLexpreResponse = {
    meta: Meta
    stats: {
        // No período (pela data de saída do setor, como na v1).
        resolvidos_total: WithComparison // manuais + automáticos
        organizados_manualmente: WithComparison
        organizados_e_peticionados_automaticamente: WithComparison
        cancelados: WithComparison
        protocolados_total: WithComparison // das resolvidas no período, quantas chegaram a ser protocoladas
        media_tempo_resolvidos: number
        mediana_tempo_resolvidos: number
        comparativo_tempo_medio_resolvidos: number | null
        comparativo_mediana_tempo_resolvidos: number | null
        // Acumulados (não dependem do período).
        represados: number
        devolvido_pendencia: number
        comparativo_devolvido_pendencia: number | null // devoluções no período vs mês anterior
    }
    resolvidos_total_por_materia: Point[]
    protocolados_total_por_materia: Point[]
    nao_organizados_total_por_materia: Point[] // represados por matéria
    resolvidos_total_por_mes: Point[] // name = 'nov 2026' (API) ou 'AAAA-MM' (mock)
    nao_resolvidos_total_por_mes: Point[] // represados por mês de entrada
    resolvidos_por_dia_org: Point[] // name = 'AAAA-MM-DD'
    resolvidos_por_funcionario: Point[]
    nao_organizados_por_funcionario: Point[]
    protocolados_por_funcionario: Point[]
    media_resolvidos_por_funcionario: Point[]
    valor_causa_por_funcionario: Point[]
    valor_causa_protocolado_por_funcionario: Point[] // parte já protocolada de valor_causa_por_funcionario
    // Quem gere a unidade vê de todos; os demais, só a própria linha.
    comissionamento_por_funcionario?: {
        funcionario: string
        qtd_protocolados: number
        valor_causa_protocolado: number
        valor_comissao: number
    }[]
    // Novo na V2 (o modal da v1): por matéria reunida (pacote), as demandas com o cliente e as rubricas.
    rubricas_reunidas?: RubricaReunida[]
    // KPIs do período: LexPre; ou legado (NG / LARJ / LAAM) quando o período não tem resolvidos no LexPre.
    fonte_indicadores?: 'lexpre' | 'legado'
    opcoes_filtro: {
        materias: string[]
        funcionarios: string[]
        ufs: string[]
        areas: { id: number; nome: string }[]
    }
}
