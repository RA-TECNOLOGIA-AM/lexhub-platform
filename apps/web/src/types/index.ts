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
    // Só para o Desenvolvedor: unidades em que o dashboard está desligado (some para os outros) e o menu de
    // ligar/desligar no card. Quem não é Dev não recebe as unidades desligadas.
    disabled_units?: string[]
    can_toggle?: boolean
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
    // Comercial (LexPre): atendente, canal de origem (a v1 usa um só) e rubrica (uma só).
    atendente_comercial?: string[]
    segmento_comercial?: string[]
    rubrica?: string[]
    // Protocolo (banco legado): sistema de protocolo (a v1 usa um só).
    sistema?: string[]
    // Financeiro Estratégico: os filtros da página (origem, ano de ajuizamento) e os seletores próprios da seção
    // Conversão (conv_*) e do modal de Clientes Pendentes (pend_*: ano e mês do TED).
    origem?: string[]
    ano_ajuizamento?: string[]
    conv_ano_ajuizamento?: string[]
    conv_ano_financeiro?: string[]
    pend_ano?: string[]
    pend_mes?: string[]
    // Execução Condenação e Execução Acordos (LexFlow): os parâmetros das rotas da v1. Subfase e comarca valem
    // para a página; os _execucao / _execucao_acordos são os seletores das seções Atividades e Diligências.
    subfase?: string[]
    comarca?: string[]
    funcionario_execucao?: string[]
    atividade_execucao?: string[]
    situacao_execucao?: string[]
    status_execucao?: string[]
    diligencia_tipo_execucao?: string[]
    diligencia_colaborador_execucao?: string[]
    tipo_acao_execucao_acordos?: string[]
    tipo_sentenca_execucao_acordos?: string[]
    numero_processo_execucao_acordos?: string[]
    funcionario_execucao_acordos?: string[]
    atividade_execucao_acordos?: string[]
    situacao_execucao_acordos?: string[]
    status_execucao_acordos?: string[]
    diligencia_tipo_execucao_acordos?: string[]
    diligencia_colaborador_execucao_acordos?: string[]
    // Execução Estratégico Geral: Ambos (sem o filtro) / condenacao / acordos. Só o front usa (como na v1).
    escopo?: string[]
    // Tickets (banco NG): um valor de cada, como os pares selection_dim/selection_value da v1
    ticket_servidor?: string[]
    ticket_categoria?: string[]
    ticket_subcategoria?: string[]
    ticket_status?: string[]
    // Julgados Acórdãos e Sentenças (LexFlow): os filtros cumulativos da v1 (sufixo _julgados) e a situação do processo.
    materia_julgados?: string[]
    relator_julgados?: string[] // acórdãos: relator (2G)
    juiz_julgados?: string[] // sentenças: juiz (1G)
    comarca_julgados?: string[]
    competencia_julgados?: string[]
    categoria_julgados?: string[] // procedente | improcedente | extinto
    uf_julgados?: string[]
    motivo_extincao_julgados?: string[]
    ano_ajuizamento_julgados?: string[]
    resultado_embargos_julgados?: string[] // Status Resultante dos embargos ('Revertido Ganho', 'Status Mantido'...)
    // Recursal (LexFlow): os filtros da página da v1 (os dos processos com o sufixo _recursal) e os da seção Atividades
    id_1g_recursal?: string[]
    id_2g_recursal?: string[]
    decisao_recursal?: string[]
    juiz_recursal?: string[]
    relator_recursal?: string[]
    materia_recursal?: string[]
    competencia_recursal?: string[]
    vara_recursal?: string[]
    subfase_recursal?: string[]
    extinto_2g_recursal?: string[]
    funcionario_recursos?: string[]
    atividade_recursos?: string[]
    status_recursos?: string[]
    situacao_recursos?: string[]
    // Publicações (LexFlow): os filtros da v1 com o sufixo _publicacoes (leitor e matéria com vários valores; os outros, um)
    leitor_publicacoes?: string[]
    materia_publicacoes?: string[]
    documento_publicacoes?: string[]
    tribunal_publicacoes?: string[]
    orgao_publicacoes?: string[]
    atividade_agendamento_publicacoes?: string[]
    setor_agendamento_publicacoes?: string[]
    status_agendamento_publicacoes?: string[]
    // Pendências Intermediárias (LexFlow): os da seção da v1 (na v1, o NG manda com _ng; a API faz a troca)
    funcionario_intermediarias?: string[]
    atividade_intermediarias?: string[]
    // Emendas e Manifestações (LexFlow): os mesmos nomes da v1 nas duas unidades; a UF só existe no NG
    funcionario_emendas_manifestacoes?: string[]
    atividade_emendas_manifestacoes?: string[]
    uf_emendas_manifestacoes?: string[]
    // Réplicas (LexFlow): os da seção da v1 (na v1, o NG manda com _ng; a API faz a troca)
    funcionario_replicas?: string[]
    atividade_replicas?: string[]
    situacao_processo?: string[] // ATIVO | SUSPENSO/SOBRESTADO | ARQUIVADO (sem nenhum = recorte padrão da query)
}

export type DashboardQuery = {
    org: string
    unit: string
    from?: string
    to?: string
    filters?: DashboardFilters
    signal?: AbortSignal // cancela a busca (ex.: o filtro mudou de novo antes da resposta)
}

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
    protocolados_por_mes: Point[] // name = 'nov 2026' na API (igual à v1); 'AAAA-MM' no mock (lib/charts.ts lê os dois)
    represados_por_mes: Point[] // idem
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
        comparativo_mediana_tempo_resolvidos_pendencia?: number | null
        // Acumulados (não dependem do período).
        pendencias_nao_resolvidas: number
        pendencias_nao_resolvidas_com_atraso: number // em aberto há mais de 5 dias
        pendencias_triagem: number
        pendencias_nao_resolvidas_reajuizamento?: number // o LexPre ainda não registra: 0
        pendencias_resolvidas_reajuizamento?: number
    }
    pendencias_resolvidas_por_dia: Point[] // name = 'AAAA-MM-DD'
    pendencias_resolvidas_por_mes?: Point[] // name = 'nov 2026' (API) ou 'AAAA-MM' (mock)
    pendencias_nao_resolvidas_por_origem: Point[] // setor de onde a pendência veio
    media_pendencias_resolvidas_por_funcionario: Point[] // resolvidas por dia, por pessoa (todos veem)
    // Quem gere a unidade vê de todos; os demais, só a própria linha. Taxas em %.
    comissionamento_pendencias_por_funcionario: {
        funcionario: string
        taxa_resolvido: number
        taxa_cancelamento: number
        qtd_resolvido: number
        valor: number
        qtd_x_valor: number
        comissao: number
    }[]
    opcoes_filtro?: {
        funcionarios?: string[]
        ufs?: string[]
        areas?: { id: number; nome: string }[]
    }
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
    can_revoke: boolean // quem pergunta pode cancelar (Gestor: só convite inteiro nas unidades dele)
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

// Uma barra de uso do plano ("Assentos 42 de 60", "Histórico 24 de 24 meses"). total null = sem teto.
export type PlanUsage = { key: string; label: string; used: number; total: number | null; unit?: string }

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
// audit = vê a Auditoria (Owner/Desenvolvedor). billing = vê Plano e cobrança (Owner/Desenvolvedor e equipe RA).
// clients = vê Clientes (Owner/Desenvolvedor da LexGroup, dona da plataforma, e equipe RA).
export type AdminPermissions = {
    access: boolean
    members: boolean
    sources: boolean
    audit: boolean
    billing: boolean
    clients: boolean
}

// O que o editor grava (api.update_member_access): estado desejado nas unidades geridas.
export type MemberAccessUpdate = {
    units: { code: string; role: UnitRoleKey }[]
    teams: string[] // ids
    org_role: 'admin' | 'member' | null // null = não muda
}

// Auditoria: o que aconteceu na organização (entradas, exportações, acesso, suporte, fontes).
// source = unidades e fontes (criar/editar unidade, sincronização); other = evento que a tela ainda não conhece
export type AuditKind = 'login' | 'export' | 'access' | 'support' | 'source' | 'other'

// Um evento como vem do banco (api.list_audit); services/auditEvents.ts traduz para AuditEvent.
export type RawAuditEvent = {
    id: string
    at: string
    action: string // 'dashboard.export', 'member.invited'...
    actor: string // nome na organização, e-mail ou 'Sistema'
    actorEmail?: string | null // a conta usada (auth.users); null = sistema. Opcional: banco antigo não manda
    targetType: string | null
    targetId: string | null
    targetName: string | null // nome do dashboard, da unidade ou da pessoa, quando dá para achar
    metadata: Record<string, unknown>
}

export type AuditEvent = {
    id: string
    at: string // ISO com fuso ('2026-10-30T14:02:00-04:00'); a tela formata
    actor: string // quem fez ("Ana Ribeiro", "Sistema", "Suporte RA Tecnologia")
    email: string | null // a conta usada por quem fez; null = sistema
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
    seats: { used: number; total: number | null } // total null = sem teto
    failingSources: number // fontes atrasadas ou com falha agora
    billing: 'ok' | 'onboarding_paid' | 'overdue'
}

export type ClientsResponse = {
    clients: PlatformClient[]
    monthlyRevenue: number | null // null = preços ainda não definidos (mostra R$ [—])
}

// Unidades e fontes: de onde vêm os dados de cada unidade (conectores).
export type SourceKind = 'database' | 'flow' | 'finance' | 'sheet' // define o ícone
// pending = falta autorizar (ex.: Conta Azul); waiting = conectada, mas ainda não sincronizou nenhuma vez;
// no_dashboards = conectada, mas nenhum dashboard ligado na unidade usa a fonte (o analista liga depois);
// disabled = a TI da LexGroup desligou a fonte (pausa: o segredo fica salvo, a API não lê)
export type SourceStatus = 'healthy' | 'late' | 'pending' | 'waiting' | 'no_dashboards' | 'disabled'
// Como a API conecta na fonte (app.data_sources.connector)
export type SourceConnector = 'lexpre' | 'lexflow' | 'internal' | 'postgres' | 'mysql' | 'sheets'
// product = contratado pela organização (LexFlow, LexPre); connection = conectada por uma unidade (banco, planilha)
export type SourceGroup = 'product' | 'connection'

export type DataSource = {
    id: string
    kind: SourceKind
    connector: SourceConnector
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
    // Banco: host, port, database, user, ssl. Planilha: tab. Nunca a senha nem o link.
    config: Record<string, unknown>
    writerAck: boolean // salva com um usuário que pode escrever ("Salvar mesmo assim")
    enabled: boolean // false = desligada pela TI da LexGroup (religar não pede o segredo de novo)
    // TI da LexGroup numa fonte com o segredo no banco: testar, trocar senha, ligar/desligar, desconectar
    canManage: boolean
    technical: SourceTechnical | null // só para a TI da LexGroup; null para os demais
}

// Para o analista escrever as queries: a chave da fonte e a estrutura salva no teste de conexão.
// schema: banco = { 'public.processo': [['id', 'integer'], ...] }; planilha = { ABA: [['COLUNA', ''], ...] }
export type SourceTechnical = {
    key: string
    schema: Record<string, [string, string][]> | null
}

// Conectar fonte: banco próprio da operação e planilha publicada (rotas da API, app/routes/source_connections.py).
export type DatabaseConnector = 'postgres' | 'mysql'

export type DatabaseConnectInput = {
    connector: DatabaseConnector
    name: string
    host: string
    port: number | null // null = a padrão (5432 / 3306)
    database: string
    user: string
    password: string
    ssl: boolean
    writerAck: boolean // true = "Salvar mesmo assim" com um usuário que pode escrever
}

export type SheetConnectInput = { connector: 'sheets'; name: string; url: string; tab: string }

export type ConnectInput = DatabaseConnectInput | SheetConnectInput

// Uma checagem do teste (rede, login, leitura, só leitura). warn = não impede salvar.
export type SourceCheck = {
    key: 'network' | 'login' | 'read' | 'readOnly'
    ok: boolean
    message: string
    ms: number
    severity: 'error' | 'warn'
    skipped: boolean
}

// Testar e salvar: saved=false = nada gravado (o teste falhou ou falta confirmar o usuário que escreve).
export type ConnectResult = {
    saved: boolean
    needsWriterAck: boolean
    checks: SourceCheck[]
    source: DataSource | null
}

export type SourceTestResult = { ok: boolean; checks: SourceCheck[] }

export type SheetTab = { name: string; rows: number }

export type ConnectInfo = {
    ready: boolean // a API tem a chave para cifrar senhas (sem ela, só LexPre/LexFlow)
    egressIp: string | null // o IP que a operação libera no firewall do banco
}

// Trocar a senha (banco) ou o link (planilha).
export type SecretInput = { password?: string; url?: string; writerAck: boolean }

export type SourcesResponse = {
    syncEveryMin: number // intervalo da sincronização (a tela monta o texto do cabeçalho)
    units: UnitSources[]
    unitLimit: { used: number; total: number } | null // "3 de 5 unidades do plano"; null = o plano não limita
    canManageUnits: boolean // Owner/Desenvolvedor: criar unidade e editar nome/fuso
    canManageSources: boolean // só Owner/Desenvolvedor da LexGroup: conectar e gerenciar fontes
}

// Conectar fonte: os produtos Lex cujo escritório se escolhe numa lista do banco do produto.
export type ProductKey = 'lexpre' | 'lexflow'

// Um escritório no banco do produto (GET /sources/{product}/offices).
export type ProductOffice = {
    ref: string // id no banco do produto
    name: string
    activity: number // número para a TI reconhecer o escritório (o texto vem em activityLabel)
    linkedTo: { org: string; unit: string; unitName: string } | null // já ligado (qualquer organização)
}

export type ProductOffices = {
    product: ProductKey
    activityLabel: string // 'movimentações nos últimos 30 dias', 'processos'
    offices: ProductOffice[]
}

// O que o formulário de unidade grava (api.create_unit / api.update_unit). O código só vale na criação.
export type UnitInput = {
    code: string
    name: string
    timezone: string
}

// Exportar (como na v1, o servidor gera o arquivo): o relatório com o período e os filtros em uso.
export type ExportRequest = DashboardQuery & {
    dashboard: string // a key ('protocolo-lexpre')
    format: 'csv' | 'xlsx'
    campos: string[] // slugs na ordem das colunas
    relatorio?: string // outro relatório do dashboard (?relatorio=), ex.: 'atividades' nos Acordos
    opcoes?: Record<string, string> // escolhas da janela (?criterio=saida, ?view=por_prazo)
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

// Uma notificação do sino (api.list_my_notifications). Tipo novo = um valor a mais em kind.
export type AppNotification = {
    id: string
    kind: 'access_request.approved'
    title: string
    body: string | null
    link: string | null // caminho dentro do app (ex.: /lexgroup/dashboards)
    created_at: string // ISO
    read_at: string | null // null = não lida
}

export type NotificationsResponse = {
    items: AppNotification[] // as últimas, mais recentes primeiro
    unread: number // total não lido (pode ser maior que o que veio em items)
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
