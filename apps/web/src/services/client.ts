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
    AuditResponse,
    ClientsResponse,
    SourcesResponse,
    ExportRequest,
    ExportFile,
    AccessRequest,
    ApprovalOrg,
    ApprovalTarget,
} from '../types/index.ts'

// A única porta de entrada para dados. As telas só conhecem esta interface;
// trocar o mock pela API real = escrever outra implementação e mudar createDataClient.
export interface DataClient {
    // Sessão. Sem sessão, os outros métodos rejeitam com DataError 401.
    signIn(email: string, password: string): Promise<void>
    // Login com a conta Google (corporativa ou não).
    // 'redirecting' = o navegador está indo para o Google (API) e volta em /login;
    // 'signed-in' = já entrou sem sair do app (mock).
    signInWithGoogle(): Promise<'redirecting' | 'signed-in'>
    signOut(): Promise<void>
    // E-mail de quem está logado (null = sem sessão). Serve à tela "sem acesso", quando o /me dá 403.
    getSessionEmail(): Promise<string | null>
    // org = slug da organização ativa (vem da URL); sem org, a organização padrão da pessoa.
    // Organização de que a pessoa não faz parte: rejeita com 403.
    getMe(org?: string): Promise<Me>
    listDashboards(org: string): Promise<DashboardCatalog>
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
    // O que a pessoa gere na organização (o menu esconde Acesso de quem não gere).
    getMyAdminPermissions(org: string): Promise<AdminPermissions>
    getAudit(org: string): Promise<AuditResponse>
    getSources(org: string): Promise<SourcesResponse>
    // Plataforma (só equipe RA): todas as organizações. Sem platform_staff, rejeita com 403.
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
