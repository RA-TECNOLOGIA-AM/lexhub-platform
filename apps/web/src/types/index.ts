// Formato das respostas. Os nomes seguem a v1 (ProtocoloLexpreNGResponse /
// PendenciaLexpreNGResponse) para a conferência v2 x v1 ser campo a campo.

export type User = {
    name: string
    initials: string
    roleLabel: string
    canExport: boolean
    canSeeCommission: boolean
    platformStaff: boolean // equipe RA: vê a seção "Plataforma" (Clientes)
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
    // Decididos pelo servidor (regra: colaborador exporta só o próprio setor; admin, dev e controller, qualquer um).
    can_export: boolean
    can_see_commission: boolean
}

export type DashboardCatalog = {
    available: DashboardSummary[]
    upcoming: { title: string; area: string }[]
}

// Novo na V2: de onde e de quando são os dados ("Atualizado há X · fuso America/Manaus").
export type Meta = { unit: string; from: string; to: string; source: string; synced_at: string; timezone: string }

export type Point = { name: string; value: number }

export type WithComparison = { total: number; comparativo: number | null }

// Filtros dos dashboards, com os nomes dos parâmetros da v1. Vários valores = lista.
export type DashboardFilters = {
    materia?: string[]
    funcionario?: string[]
    area_atuacao_id?: string[]
    uf?: string[]
}

export type DashboardQuery = { org: string; unit: string; from?: string; to?: string; filters?: DashboardFilters }

// Campos da v1 (ProtocoloLexpreNGResponse) + o que é novo da V2 (marcado abaixo).
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
        // Situação atual: não dependem do período.
        represados: number
        devolvido_peticionamento: number
        devolvido_org_doc: number
        devolvido_pendencia: number
        comparativo_devolvido_peticionamento: number | null
        comparativo_devolvido_org_doc: number | null
        comparativo_devolvido_pendencia: number | null
    }
    protocolados_por_dia: Point[]
    protocolados_por_materia: Point[]
    represados_por_materia: Point[]
    protocolados_por_funcionario: Point[]
    represados_por_funcionario: Point[]
    media_protocolados_por_funcionario: Point[]
    valor_causa_por_funcionario: Point[]
    protocolados_por_mes: Point[] // name = 'AAAA-MM'
    represados_por_mes: Point[] // name = 'AAAA-MM'
    // Só vem para quem tem permissão (can_see_commission).
    comissionamento_por_funcionario?: { funcionario: string; qtd_protocolados: number; valor_comissao: number }[]
    // --- Novos na V2 (não existem na v1) ---
    protocolados_no_prazo: { taxa: number; comparativo: number | null } // taxa em %
    metas: { tempo_medio_dias: number; no_prazo_pct: number; protocolados_por_funcionario: number }
    pendencias_mais_antigas: { processo: string; etapa: string; responsavel: string; dias_parado: number }[]
    opcoes_filtro: {
        materias: string[]
        funcionarios: string[]
        ufs: string[]
        areas: { id: number; nome: string }[]
    }
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
// --- Membros ---
export type RoleKey = 'owner' | 'admin' | 'gestor' | 'colaborador' | 'leitor'
// Banco: invited / active / disabled. 'requested' = pediu acesso e espera aprovação (novo na V2).
export type MemberStatus = 'active' | 'invited' | 'requested' | 'disabled'

export type Member = {
    id: string
    name: string | null // null = convite ainda não aceito (mostra o e-mail no lugar)
    email: string
    role: RoleKey | null // null = sem papel (pedido ainda não aprovado)
    units: string[] // códigos ('NG', 'LA_AM'...); ['*'] = todas as unidades
    team: string | null
    status: MemberStatus
    note: string | null // linha de baixo, quando não é o e-mail ("Convidado por Ana Ribeiro há 2 dias")
    security: string | null // 'MFA ativo', 'Google'...
}

export type Team = { name: string; dashboards: number } // quantos dashboards a equipe vê

export type InviteRequest = {
    emails: string[]
    role: Exclude<RoleKey, 'owner'> // owner não se convida: é quem cria a organização
    units: string[]
    team: string
}

export type MembersResponse = { members: Member[]; seats: { used: number; total: number }; teams: Team[] }

// Plano e cobrança. Preços ainda em descoberta: null = "a definir" (a tela mostra [PREÇO]/[VALOR]).
export type PlanKey = 'starter' | 'pro' | 'enterprise'

export type Plan = {
    key: PlanKey
    name: string
    monthlyPrice: number | null // null = ainda não definido
    custom: boolean // true = "Sob consulta" (negociado caso a caso), não tem preço de tabela
    tagline: string // para quem é ("Um escritório começando a medir a operação")
    features: string[]
}

// Uma barra de uso do plano ("Assentos 42 de 60", "Histórico 24 de 24 meses").
export type PlanUsage = { key: string; label: string; used: number; total: number; unit?: string }

export type InvoiceStatus = 'paid' | 'open' | 'overdue'

export type Invoice = {
    id: string
    month: string // 'YYYY-MM'
    amount: number | null // null = valor ainda não definido
    status: InvoiceStatus
    nfse: 'issued' | 'pending'
}

export type BillingResponse = {
    current: {
        plan: PlanKey
        status: 'active' | 'past_due' | 'canceled'
        renewsOn: string // 'YYYY-MM-DD'
        paymentMethods: string[] // ['boleto', 'PIX']
        gateway: string | null // null = gateway ainda não escolhido
    }
    usage: PlanUsage[]
    plans: Plan[]
    invoices: Invoice[] // mais recente primeiro
}

// Acesso: o que cada papel pode fazer e o que cada equipe vê.
// Célula da matriz: sim, não ou "em parte" com a ressalva ("Só os seus", "Da unidade").
export type AccessCell = { kind: 'yes' } | { kind: 'no' } | { kind: 'partial'; note: string }

export type Permission = {
    key: string // estável, para o código procurar a linha ('export', 'members'...)
    label: string // texto da linha ("Exportar e gerar PDF")
    cells: Record<RoleKey, AccessCell> // uma célula por papel
}

// Regra de dashboards de uma equipe: nas unidades em que a pessoa estiver, ela vê estes dashboards.
export type TeamRule = {
    team: string
    people: number
    dashboards: string[]
    all: boolean // true = todos os dashboards das suas unidades (Diretoria); aí `dashboards` fica vazio
    scope: string | null // observação ("Colaborador vê só os próprios atendimentos...")
}

export type AccessResponse = {
    matrix: Permission[]
    rules: TeamRule[]
}

// Auditoria: o que aconteceu na organização (entradas, exportações, acesso, suporte, fontes).
export type AuditKind = 'login' | 'export' | 'access' | 'support' | 'source'

export type AuditEvent = {
    id: string
    at: string // ISO com fuso ('2026-10-30T14:02:00-04:00'); a tela formata
    actor: string // quem fez ("Ana Ribeiro", "Sistema", "Suporte RA Tecnologia")
    kind: AuditKind
    action: string // "Exportou dados"
    detail: string
}

export type AuditResponse = { events: AuditEvent[] } // mais recente primeiro

// Plataforma (só equipe RA): as organizações clientes.
export type ClientPlan = PlanKey | 'onboarding' // 'onboarding' = em implantação, antes de assinar um plano

export type PlatformClient = {
    slug: string // endereço da organização (lexhub.app/<slug>)
    name: string
    sub: string // "3 unidades · cliente desde a v1"
    plan: ClientPlan
    seats: { used: number; total: number }
    failingSources: number // fontes atrasadas ou com falha agora
    billing: 'ok' | 'onboarding_paid' | 'overdue'
}

export type ClientsResponse = {
    clients: PlatformClient[]
    monthlyRevenue: number | null // null = preços ainda não definidos (mostra R$ [—])
}
