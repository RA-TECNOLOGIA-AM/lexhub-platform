import { createApiClient } from './apiClient.ts'
import { withSessionCache } from './sessionCache.ts'
import { env, required } from './env.ts'
import { createHttp } from './http.ts'
import { createMockClient } from './mockClient.ts'
import { createSupabaseAuth } from './supabase.ts'
import type {
    DashboardCatalog,
    DashboardQuery,
    Me,
    Meta,
    PendenciasResponse,
    ProtocoloResponse,
    InviteRequest,
    InviteResult,
    Member,
    MembersResponse,
    BillingResponse,
    AccessOverview,
    AdminPermissions,
    MemberAccessUpdate,
    AuditQuery,
    AuditResponse,
    ClientsResponse,
    DataSource,
    SourceDetail,
    SourcesFreshness,
    SourcesResponse,
    UnitInput,
    UnitSources,
    ProductKey,
    ProductOffices,
    ConnectInfo,
    ConnectInput,
    ConnectResult,
    SecretInput,
    SheetTab,
    SourceTestResult,
    ExportRequest,
    ExportFile,
    AccessRequest,
    ApprovalOrg,
    ApprovalTarget,
    NotificationsResponse,
} from '../types/index.ts'

export type DeviceCodeResponse = {
    device_code: string
    user_code: string
    verification_uri: string
    interval: number
    expires_in: number
}

export type DeviceSession = {
    access_token: string
    refresh_token: string
    expires_in: number
}

export type DeviceTokenResult =
    | { status: 'authorization_pending' | 'slow_down' }
    | { status: 'expired_token' }
    | ({ status: 'approved' } & DeviceSession)

// A única porta de entrada para dados. As telas só conhecem esta interface;
// trocar o mock pela API real = escrever outra implementação e mudar createDataClient.
export interface DataClient {
    // Sessão. Sem sessão, os outros métodos rejeitam com DataError 401.
    signIn(email: string, password: string): Promise<void>
    // Login com a conta Google (corporativa ou não).
    // 'redirecting' = o navegador está indo para o Google (API) e volta em /login;
    // 'signed-in' = já entrou sem sair do app (mock).
    signInWithGoogle(returnTo?: string): Promise<'redirecting' | 'signed-in'>
    // Sai só deste aparelho (TV e celular saem cada um por si).
    signOut(): Promise<void>
    // Encerra as sessões da conta em todos os outros aparelhos (ex.: TVs esquecidas); este continua logado.
    signOutOthers(): Promise<void>
    // A sessão deste aparelho ainda existe no servidor? false = foi derrubada (ex.: por outro aparelho).
    // Erro de rede responde true: na dúvida, não tira a pessoa.
    isSessionAlive(): Promise<boolean>
    // E-mail de quem está logado (null = sem sessão). Serve à tela "sem acesso", quando o /me dá 403.
    getSessionEmail(): Promise<string | null>
    getSessionAccessToken(): Promise<string | null>
    createDeviceCode(): Promise<DeviceCodeResponse>
    pollDeviceToken(deviceCode: string): Promise<DeviceTokenResult>
    authorizeDevice(userCode: string): Promise<void>
    setDeviceSession(session: DeviceSession): Promise<void>
    // org = slug da organização ativa (vem da URL); sem org, a organização padrão da pessoa.
    // Organização de que a pessoa não faz parte: rejeita com 403.
    getMe(org?: string): Promise<Me>
    listDashboards(org: string): Promise<DashboardCatalog>
    // Liga/desliga um dashboard numa unidade (só o Desenvolvedor; a API nega os outros com 403).
    setDashboardEnabled(org: string, unit: string, dashboardKey: string, enabled: boolean): Promise<void>
    listFavorites(org: string): Promise<string[]>
    // Membros (schema api no Supabase): o servidor só devolve e aceita o que quem chama gere.
    listMembers(org: string): Promise<MembersResponse>
    inviteMembers(org: string, invite: InviteRequest): Promise<InviteResult>
    setMemberStatus(org: string, memberId: string, status: 'active' | 'disabled'): Promise<Member>
    revokeInvitation(id: string): Promise<void>
    // Logo depois do login: convites pendentes do e-mail verificado viram associação. Devolve quantos.
    acceptMyInvitations(): Promise<number>
    setFavorite(org: string, dashboardKey: string, favorite: boolean): Promise<void>
    // Ordem dos cards do hub da pessoa: uma lista de keys para o hub inteiro ([] = ordem do catálogo).
    getHubOrder(org: string): Promise<string[]>
    setHubOrder(org: string, keys: string[]): Promise<void>
    getBilling(org: string): Promise<BillingResponse>
    // Acesso (schema api no Supabase): grade da unidade (null = a primeira gerida) e edição de uma pessoa.
    getAccessOverview(org: string, unit: string | null): Promise<AccessOverview>
    updateMemberAccess(org: string, memberId: string, update: MemberAccessUpdate): Promise<Member>
    // Grupos de um setor (colunas inteiras) e, só Owner/Desenvolvedor, "vê tudo" (null = não muda).
    setTeamGroups(org: string, teamId: string, groups: string[], seesAll: boolean | null): Promise<void>
    // O que a pessoa gere na organização (o menu esconde Acesso de quem não gere).
    getMyAdminPermissions(org: string): Promise<AdminPermissions>
    // Auditoria filtrada no banco por período e tipo.
    getAudit(org: string, query: AuditQuery): Promise<AuditResponse>
    // Abriu um dashboard (vai para a Auditoria). Quem chama ignora falha: nunca impede o dashboard de abrir.
    logDashboardView(org: string, unit: string, dashboardKey: string): Promise<void>
    // Registra na própria auditoria que ela foi exportada (com o filtro e quantos eventos). Falhou = não baixa.
    logAuditExport(org: string, filter: { kind: string; actor: string }, rows: number): Promise<void>
    getSources(org: string): Promise<SourcesResponse>
    // Uma fonte vista de uma unidade (o modal). Unidade fora do escopo = 403; fonte que ela não usa = 409.
    getSourceDetail(org: string, unit: string, source: string): Promise<SourceDetail>
    // A hora de cada fonte no cache da API, o mesmo dado do card do hub (só memória: não consulta os bancos).
    getSourcesFreshness(org: string, keys: string[]): Promise<SourcesFreshness>
    // Owner/Desenvolvedor: criar unidade e mudar nome/fuso (o código não muda). Regra quebrada = 409 com a mensagem.
    createUnit(org: string, unit: UnitInput): Promise<UnitSources>
    updateUnit(org: string, unit: UnitInput): Promise<UnitSources>
    // Conectar fonte (só a TI da LexGroup; os outros recebem 403). A lista vem do banco do produto (API);
    // ligar grava a ref da unidade (Supabase). Escritório já ligado / unidade já ligada = 409 com a mensagem.
    listProductOffices(product: ProductKey): Promise<ProductOffices>
    linkProductOffice(org: string, unit: string, product: ProductKey, ref: string): Promise<UnitSources>
    // Banco próprio e planilha (só a TI da LexGroup). O teste nunca é erro: saved/ok + as checagens.
    getConnectInfo(): Promise<ConnectInfo>
    inspectSheet(url: string): Promise<SheetTab[]> // link inválido ou que não baixa = 422 com a mensagem
    connectSource(org: string, unit: string, input: ConnectInput): Promise<ConnectResult>
    retestSource(org: string, source: string): Promise<SourceTestResult>
    changeSourceSecret(org: string, source: string, input: SecretInput): Promise<ConnectResult>
    disconnectSource(org: string, source: string): Promise<void>
    // Ligar/desligar (pausa reversível; a API limpa o cache na hora). Devolve a fonte com o status novo.
    setSourceEnabled(org: string, source: string, enabled: boolean): Promise<DataSource>
    // Plataforma: todas as organizações. Só Owner/Desenvolvedor da LexGroup e equipe RA; os outros recebem 403.
    listClients(): Promise<ClientsResponse>
    getProtocolo(query: DashboardQuery): Promise<ProtocoloResponse>
    getPendencias(query: DashboardQuery): Promise<PendenciasResponse>
    // Dados de qualquer dashboard pela key (o formato T é definido na pasta do dashboard).
    // No mock: só o `meta` e `stats` vazio (os números de verdade só vêm da API).
    getDashboardData<T extends { meta: Meta }>(dashboardKey: string, query: DashboardQuery): Promise<T>
    // Relatório de um dashboard (CSV ou XLSX). Sem can_export ou sem acesso à unidade, rejeita com 403.
    exportDashboard(request: ExportRequest): Promise<ExportFile>

    // Pedidos de acesso. Quem pede: logado e sem associação ativa (já tem acesso ou pedido pendente = 409).
    requestAccess(office: string, message: string | null): Promise<AccessRequest>
    getMyAccessRequest(): Promise<AccessRequest | null> // o último pedido (null = nunca pediu)
    // Equipe RA (sem platform_staff = 403).
    countPendingAccessRequests(): Promise<number>
    listAccessRequests(status: 'pending' | 'decided'): Promise<AccessRequest[]>
    getApprovalOptions(): Promise<ApprovalOrg[]>
    approveAccessRequest(id: string, target: ApprovalTarget): Promise<AccessRequest>
    rejectAccessRequest(id: string, note: string | null): Promise<AccessRequest>

    // Notificações do sino: só as de quem está logado.
    listMyNotifications(): Promise<NotificationsResponse>
    markNotificationsRead(ids: string[] | null): Promise<void> // null = todas

    // Foto de perfil de quem está logado (bucket 'avatars'). Envia a imagem já cortada e devolve o caminho novo.
    uploadMyAvatar(image: Blob): Promise<string>
    removeMyAvatar(): Promise<void>
    // URL pública da foto a partir do avatar_path do /me.
    avatarUrl(path: string): string
}

// mock = dados fictícios; api = Supabase Auth (login) + API V2 (dados). Escolha em VITE_DATA_SOURCE.
function createDataClient(): DataClient {
    if (env.dataSource === 'mock') return createMockClient()
    if (env.dataSource === 'api') {
        const auth = createSupabaseAuth(
            required('VITE_SUPABASE_URL', env.supabaseUrl),
            required('VITE_SUPABASE_ANON_KEY', env.supabaseAnonKey),
        )
        const http = createHttp({
            baseUrl: required('VITE_BASE_API_URL', env.apiUrl),
            getToken: async () => (await auth.auth.getSession()).data.session?.access_token ?? null,
        })
        // Catálogo, favoritos e ordem em memória na sessão: voltar ao hub não espera a API (sessionCache.ts).
        // A volta do Google vem para a mesma origem em que o app está aberto: o código do PKCE fica
        // guardado no navegador por origem (outra porta = outro armazenamento = login falha).
        return withSessionCache(createApiClient({ auth, http, siteUrl: window.location.origin }))
    }
    throw new Error(`VITE_DATA_SOURCE="${env.dataSource}" inválido: use mock ou api`)
}

export const dataClient = createDataClient()
