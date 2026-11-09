import { createApiClient } from './apiClient.ts'
import { env, required } from './env.ts'
import { createHttp } from './http.ts'
import { createMockClient } from './mockClient.ts'
import { createSupabaseAuth } from './supabase.ts'
import type {
    DashboardCatalog,
    DashboardQuery,
    Me,
    PendenciasResponse,
    ProtocoloResponse,
    InviteRequest,
    MembersResponse,
    BillingResponse,
    AccessResponse,
    AuditResponse,
    ClientsResponse,
} from '../types/index.ts'

// A única porta de entrada para dados. As telas só conhecem esta interface;
// trocar o mock pela API real = escrever outra implementação e mudar createDataClient.
export interface DataClient {
    // Sessão. Sem sessão, os outros métodos rejeitam com DataError 401.
    signIn(email: string, password: string): Promise<void>
    signOut(): Promise<void>
    // org = slug da organização ativa (vem da URL); sem org, a organização padrão da pessoa.
    // Organização de que a pessoa não faz parte: rejeita com 403.
    getMe(org?: string): Promise<Me>

    listDashboards(org: string): Promise<DashboardCatalog>
    listFavorites(org: string): Promise<string[]>
    listMembers(org: string): Promise<MembersResponse>
    inviteMembers(org: string, invite: InviteRequest): Promise<void>
    setFavorite(org: string, dashboardKey: string, favorite: boolean): Promise<void>
    getBilling(org: string): Promise<BillingResponse>
    getAccess(org: string): Promise<AccessResponse>
    getAudit(org: string): Promise<AuditResponse>
    // Plataforma (só equipe RA): todas as organizações. Sem platformStaff, rejeita com 403.
    listClients(): Promise<ClientsResponse>
    getProtocolo(query: DashboardQuery): Promise<ProtocoloResponse>
    getPendencias(query: DashboardQuery): Promise<PendenciasResponse>
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
        return createApiClient({ auth, http })
    }
    throw new Error(`VITE_DATA_SOURCE="${env.dataSource}" inválido: use mock ou api`)
}

export const dataClient = createDataClient()
