import type { Meta, Point, WithComparison } from '../../../types/index.ts'
import type { RubricaReunida } from '../setor/rubricas.ts'

// Resposta do dashboard Peticionamento (LexPre): os campos da v1 (PeticionamentoLexpreNGResponse) que a tela
// usa + `opcoes_filtro` (novo na V2). Tempos em dias; comparativos em % vs mês anterior.
export type PeticionamentoLexpreResponse = {
    meta: Meta
    stats: {
        // No período (pela data de saída do setor, como na v1).
        total_peticionados: WithComparison // confeccionados (não cancelados) = manuais + automáticos
        peticionados_manualmente: WithComparison
        peticionados_automaticamente: WithComparison // pet_auto
        cancelados: WithComparison
        protocolados_total: WithComparison // dos confeccionados, quantos foram protocolados no período
        valor_causa_confeccionado: WithComparison
        ticket_medio_confeccionado: WithComparison
        media_tempo_peticionado: number
        mediana_tempo_peticionado: number
        comparativo_tempo_medio_peticionado: number | null
        comparativo_mediana_tempo_peticionado: number | null
        // Situação atual do setor (totais, não dependem do período).
        represados: number // "Não peticionados"
        // Só quando os KPIs vêm do legado NG/RJ (existia na página antiga; a LA não tinha).
        processos_em_revisao?: number | null
        retorno_org_doc: number
        retorno_pendencia: number
        comparativo_retorno_org_doc: number | null
        comparativo_retorno_pendencia: number | null
    }
    peticionados_por_materia: Point[]
    protocolados_por_materia: Point[]
    represados_por_materia: Point[]
    peticionados_por_mes: Point[] // name = 'nov 2026' (API) ou 'AAAA-MM' (mock)
    represados_por_mes: Point[]
    peticionados_por_dia: Point[] // name = 'AAAA-MM-DD'
    represados_por_funcionario: Point[]
    peticionados_por_funcionario: Point[]
    protocolados_por_funcionario: Point[]
    media_peticionado_por_funcionario: Point[]
    valor_causa_por_funcionario: Point[]
    valor_causa_protocolado_por_funcionario: Point[]
    // Quem gere a unidade vê de todos; os demais, só a própria linha. Taxa em %; valores unitários em R$.
    comissionamento_por_funcionario?: {
        funcionario: string
        qtd_acoes_massa: number
        valor_acoes_massa: number
        qtd_x_valor_massa: number
        qtd_acoes_especificas: number
        valor_acoes_especificas: number
        qtd_x_valor_especificas: number
        taxa_resolvidos: number | null
        valor_comissao: number
    }[]
    // Novo na V2 (o modal da v1): por matéria reunida (pacote), as demandas resolvidas no período ou represadas
    // agora, com o cliente e as rubricas que compõem cada uma. Já com os filtros da página.
    rubricas_reunidas?: RubricaReunida[]
    // KPIs do período: LexPre; legado (só legado); ou misto (LexPre + legado no mesmo período).
    fonte_indicadores?: 'lexpre' | 'legado' | 'misto'
    opcoes_filtro: {
        materias: string[]
        funcionarios: string[]
        ufs: string[]
        areas: { id: number; nome: string }[]
    }
}
