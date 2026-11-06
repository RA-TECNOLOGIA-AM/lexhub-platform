// Formato das respostas. Os nomes seguem a v1 (ProtocoloLexpreNGResponse /
// PendenciaLexpreNGResponse) para a conferência v2 x v1 ser campo a campo.

export type User = {
    name: string
    initials: string
    roleLabel: string
    canExport: boolean
    canSeeCommission: boolean
}

export type Org = { slug: string; name: string; sub: string }

export type Unit = { code: string; name: string }

// Quem está logado, em qual organização e quais unidades enxerga.
export type Me = { user: User; org: Org; units: Unit[] }

export type DashboardSummary = {
    key: string
    title: string
    area: string
    desc: string
    units: string[]
    source: string
    synced_at: string
    max_delay_min: number
}

export type DashboardCatalog = {
    available: DashboardSummary[]
    upcoming: { title: string; area: string }[]
}

// Novo na V2: de onde e de quando são os dados ("Atualizado há X").
export type Meta = { unit: string; from: string; to: string; source: string; synced_at: string }

export type Point = { name: string; value: number }

export type WithComparison = { total: number; comparativo: number | null }

export type DashboardQuery = { org: string; unit: string; from?: string; to?: string }

export type ProtocoloResponse = {
    meta: Meta
    stats: {
        protocolados_total: WithComparison
        valor_causa_protocolado: WithComparison
        ticket_medio_protocolado: WithComparison
        media_tempo_protocolado: number
        mediana_tempo_protocolado: number
        comparativo_tempo_medio_protocolado: number | null
        comparativo_mediana_tempo_protocolado: number | null
        represados: number
        devolvido_peticionamento: number
        devolvido_org_doc: number
        devolvido_pendencia: number
    }
    protocolados_por_dia: Point[]
    protocolados_por_materia: Point[]
    protocolados_por_funcionario: Point[]
    represados_por_funcionario: Point[]
    comissionamento_por_funcionario: { funcionario: string; qtd_protocolados: number; valor_comissao: number }[]
}

export type PendenciasResponse = {
    meta: Meta
    stats: {
        pendencias_total: number
        pendencias_resolvidas: number
        pendencias_canceladas: number
        pendencias_taxa_resolvidos: number
        pendencias_taxa_nao_resolvidos: number
        pendencias_taxa_canceladas: number
        media_tempo_resolvidos_pendencia: number
        mediana_tempo_resolvidos_pendencia: number
        comparativo_pendencias_resolvidas: number | null
        comparativo_tempo_medio_resolvidos_pendencia: number | null
        pendencias_nao_resolvidas: number
        pendencias_nao_resolvidas_com_atraso: number
        pendencias_triagem: number
    }
    pendencias_resolvidas_por_dia: Point[]
    pendencias_nao_resolvidas_por_origem: Point[]
    media_pendencias_resolvidas_por_funcionario: Point[]
    comissionamento_pendencias_por_funcionario: {
        funcionario: string
        taxa_resolvido: number
        taxa_cancelamento: number
        qtd_resolvido: number
        valor: number
        qtd_x_valor: number
        comissao: number
    }[]
}