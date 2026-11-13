// Formato das respostas. Os nomes seguem a v1 (ProtocoloLexpreNGResponse /
// PendenciaLexpreNGResponse) para a conferência v2 x v1 ser campo a campo.

export type User = {
    name: string
    initials: string
    role_label: string
    can_export: boolean
    can_see_commission: boolean
    platform_staff: boolean // equipe RA: vê a seção "Plataforma" (Clientes)
}

export type Org = { slug: string; name: string; sub: string }

export type Unit = { code: string; name: string }

// Quem está logado, a organização ativa (a da URL) e as unidades que enxerga nela.
// orgs = todas as organizações de que a pessoa faz parte (lista do seletor na barra lateral).
export type Me = { user: User; org: Org; units: Unit[]; orgs: Org[] }

export type DashboardSummary = {
    key: string
    title: string
    area: string
    desc: string
    units: string[]
    source: string
    synced_at: string | null // null = a fonte ainda não sincronizou (cache de 5 min)
    max_delay_min: number
    // Decididos pelo servidor (regra: colaborador exporta só o próprio setor; admin, dev e controller, qualquer um).
    // Com várias unidades, só vale true se valer em todas (o botão nunca aparece onde a API negaria).
    can_export: boolean
    can_see_commission: boolean
}

export type DashboardCatalog = {
    available: DashboardSummary[]
    upcoming: { title: string; area: string }[]
}

// Novo na V2: de onde e de quando são os dados ("Atualizado há X · fuso America/Manaus").
export type Meta = {
    unit: string
    from: string
    to: string
    source: string
    synced_at: string | null // null = a fonte ainda não sincronizou
    timezone: string
}

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
    // Quem gere a unidade vê de todos; os demais, só a própria linha ([] sem vínculo com a fonte).
    comissionamento_por_funcionario?: { funcionario: string; qtd_protocolados: number; valor_comissao: number }[]
    // --- Novos na V2 (não existem na v1). null = regra ainda não definida (a tela mostra "—") ---
    protocolados_no_prazo: { taxa: number; comparativo: number | null } | null // taxa em %
    metas: { tempo_medio_dias: number; no_prazo_pct: number; protocolados_por_funcionario: number } | null
    pendencias_mais_antigas: { processo: string; etapa: string; responsavel: string; dias_parado: number }[] | null
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
// Papel na organização inteira (admin = Desenvolvedor; member = o acesso vem do cargo em cada unidade).
export type OrgRoleKey = 'owner' | 'admin' | 'member'
export type MemberStatus = 'active' | 'invited' | 'disabled'

// Como vem de api.list_members: cargo por unidade (só as unidades que quem pergunta gere).
export type Member = {
    id: string
    name: string
    email: string
    org_role: OrgRoleKey
    units: { code: string; role: UnitRoleKey }[]
    teams: string[]
    team_ids: string[] // mesmas equipes, por id (o nome se repete entre unidades: Diretoria)
    status: MemberStatus
    last_seen_at: string | null
    security: string | null // 'Google' quando já entrou pelo Google
}

// Convite pendente (vira associação quando a pessoa entra com o Google usando o e-mail).
export type Invitation = {
    id: string
    email: string
    role: 'admin' | UnitRoleKey // admin vale na organização; cargo de unidade vale nas unidades do convite
    units: string[]
    teams: string[]
    invited_by: string | null
    created_at: string
    expires_at: string
}

export type MemberTeam = { id: string; name: string; unit: string } // unit = código da unidade

export type InviteRequest = { emails: string[]; role: Invitation['role']; units: string[]; teams: string[] }
export type InviteResult = { invited: string[]; skipped: { email: string; reason: string }[] }

export type MembersResponse = {
    members: Member[]
    invitations: Invitation[]
    teams: MemberTeam[]
    units: Unit[] // as unidades que quem pergunta gere
    can_invite_admin: boolean
}

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
        plan: ClientPlan // 'onboarding' = em implantação, ainda sem plano assinado
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

// Colunas da matriz de papéis: os dois papéis da organização e os quatro cargos de unidade.
export type PermissionRole = 'owner' | 'admin' | UnitRoleKey

export type Permission = {
    key: string // estável, para o código procurar a linha ('export', 'members'...)
    label: string // texto da linha ("Exportar e gerar PDF")
    cells: Record<PermissionRole, AccessCell> // uma célula por papel
}

// Acesso (api.access_overview): a grade "o que cada cargo vê" de uma unidade + o que o editor precisa.
export type AccessOverview = {
    units: Unit[] // as unidades em que quem pergunta gere acesso
    unit: string // a unidade da grade
    dashboards: { key: string; title: string; area: string; teams: string[] }[] // teams = equipes que liberam
    teams: MemberTeam[] // equipes de todas as unidades geridas
    roles: { key: UnitRoleKey; sees_all: boolean; exports: boolean }[]
    rules: { team_id: string; dashboard_key: string }[] // regras das equipes de todas as unidades geridas
    dashboards_by_unit: Record<string, string[]> // keys ligadas em cada unidade gerida
    titles: Record<string, string> // key -> título
    can_set_org_role: boolean // pode tornar alguém Desenvolvedor (Owner/Desenvolvedor)
}

// O que a pessoa gere nesta organização (api.my_admin_permissions): o menu esconde o que não for dela.
// sources = vê a aba Unidades e fontes (Owner/Desenvolvedor: todas; Gestor/Controller: as próprias unidades).
export type AdminPermissions = { access: boolean; members: boolean; sources: boolean }

// O que o editor grava (api.update_member_access): estado desejado nas unidades geridas.
export type MemberAccessUpdate = {
    units: { code: string; role: UnitRoleKey }[]
    teams: string[] // ids
    org_role: 'admin' | 'member' | null // null = não muda
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

// Unidades e fontes: de onde vêm os dados de cada unidade (conectores).
export type SourceKind = 'database' | 'flow' | 'finance' | 'sheet' // define o ícone
// pending = falta autorizar (ex.: Conta Azul); waiting = conectada, mas ainda não sincronizou nenhuma vez
export type SourceStatus = 'healthy' | 'late' | 'pending' | 'waiting'
// product = contratado pela organização (LexFlow, LexPre); connection = conectada por uma unidade (banco, planilha)
export type SourceGroup = 'product' | 'connection'

export type DataSource = {
    id: string
    kind: SourceKind
    group: SourceGroup
    name: string // "LexPre · escritório 1"
    detail: string // "Comercial e pré-protocolo"
    managedBy: string | null // nome da unidade dona quando é de outra unidade (LARJ usa o banco NG); null = desta
    syncedAt: string | null // ISO da última sincronização; null = nunca sincronizou
    rows: number | null // linhas na última sincronização; null = não se aplica
    failures: number // falhas seguidas (0 = nenhuma)
    status: SourceStatus // decidido pelo servidor
}

export type UnitSources = {
    unit: Unit
    timezone: string // 'America/Manaus'
    dashboards: number // quantos dashboards essas fontes alimentam
    lastFailure: { at: string; source: string; message: string } | null // últimos 7 dias; null = nenhuma
    sources: DataSource[]
}

// Uma sincronização de uma fonte (app.source_sync_runs). ok/finishedAt null = ainda rodando.
export type SyncRun = {
    startedAt: string
    finishedAt: string | null
    ok: boolean | null
    rows: number | null
    error: string | null
}

// O modal de uma fonte, vista de uma unidade (api.source_detail).
export type SourceDetail = {
    unit: Unit
    source: DataSource
    owner: Unit | null // unidade dona; null = produto contratado pela organização
    dashboards: { key: string; name: string }[] // os desta unidade que usam a fonte
    runs: SyncRun[] // as 10 últimas, da mais recente para a mais antiga
}

export type SourcesResponse = {
    syncEveryMin: number // intervalo da sincronização (a tela monta o texto do cabeçalho)
    units: UnitSources[]
    unitLimit: { used: number; total: number } | null // "3 de 5 unidades do plano"; null = o plano não limita
}

// Exportar (como na v1, o servidor gera o arquivo): o relatório com o período e os filtros em uso.
export type ExportRequest = DashboardQuery & {
    dashboard: string // a key ('protocolo-lexpre')
    format: 'csv' | 'xlsx'
    campos: string[] // slugs na ordem das colunas
}

export type ExportFile = {
    blob: Blob
    filename: string
    note?: string // aviso para mostrar depois de baixar (ex.: no mock o XLSX sai como CSV)
}

// ---------- Pedidos de acesso (schema api do Supabase; ver supabase/migrations/*_solicitar_acesso.sql) ----------
export type AccessRequestStatus = 'pending' | 'approved' | 'rejected'

export type AccessRequest = {
    id: string
    email: string
    full_name: string
    office: string // escritório ou empresa que a pessoa informou
    message: string | null
    status: AccessRequestStatus
    created_at: string // ISO
    decided_at: string | null
    decision_note: string | null // nota da recusa
    result_org_id: string | null // organização em que entrou (aprovado)
}

// Organizações e unidades que a equipe RA pode escolher ao aprovar.
export type ApprovalOrg = {
    id: string
    slug: string
    name: string
    units: { id: string; code: string; name: string }[]
}

export type UnitRoleKey = 'gestor' | 'controller' | 'colaborador' | 'leitor'

// Para onde vai quem foi aprovado: organização existente (papel + cargo em cada unidade) ou organização nova.
export type ApprovalTarget =
    | {
          kind: 'existing'
          org_id: string
          org_role: 'admin' | 'member'
          units: { unit_id: string; role_key: UnitRoleKey }[]
      }
    | {
          kind: 'new'
          name: string
          slug: string
          org_role: 'owner' | 'admin'
          unit: { code: string; name: string; timezone: string }
      }
