import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { DataError } from './errors.ts'
import { toSearch, type Http } from './http.ts'
import type {
    BillingResponse,
    DashboardCatalog,
    Me,
    MembersResponse,
    PendenciasResponse,
    ProtocoloResponse,
    AccessResponse,
    AuditResponse,
    ClientsResponse,
} from '../types/index.ts'

// Módulo: o DataClient de verdade. Login pelo Supabase Auth; todo dado pela API V2.
// Parâmetros: o cliente de login e o http (já com a URL da API e o token).
// As rotas seguem o padrão da API: /orgs/{org}/units/{unit}/dashboards/{key}.
// Rota que a API ainda não tem responde 404 (ver apps/api/README.md).
export function createApiClient({ auth, http }: { auth: SupabaseClient; http: Http }): DataClient {
    const dashboard =
        <T>(key: string) =>
        (q: { org: string; unit: string; from?: string; to?: string; filters?: object }) =>
            http.get<T>(`/orgs/${q.org}/units/${q.unit}/dashboards/${key}${toSearch(q)}`)

    return {
        async signIn(email, password) {
            const { error } = await auth.auth.signInWithPassword({ email: email.trim(), password })
            if (error) {
                // Mesma mensagem do mock: não diz se o e-mail existe.
                throw new DataError(error.status === 400 ? 401 : (error.status ?? 0), 'E-mail ou senha incorretos.')
            }
        },

        async signOut() {
            await auth.auth.signOut()
        },

        getMe: (org) => http.get<Me>(org ? `/me?org=${encodeURIComponent(org)}` : '/me'),
        listDashboards: (org) => http.get<DashboardCatalog>(`/orgs/${org}/dashboards`),
        listMembers: (org) => http.get<MembersResponse>(`/orgs/${org}/members`),
        async inviteMembers(org, invite) {
            await http.post(`/orgs/${org}/invitations`, invite)
        },
        listFavorites: (org) => http.get<string[]>(`/orgs/${org}/favorites`),
        async setFavorite(org, dashboardKey, favorite) {
            const path = `/orgs/${org}/favorites/${dashboardKey}`
            await (favorite ? http.post(path) : http.delete(path))
        },
        getAccess: (org) => http.get<AccessResponse>(`/orgs/${org}/access`),
        getAudit: (org) => http.get<AuditResponse>(`/orgs/${org}/audit`),
        listClients: () => http.get<ClientsResponse>('/platform/clients'),
        getBilling: (org) => http.get<BillingResponse>(`/orgs/${org}/billing`),
        getProtocolo: dashboard<ProtocoloResponse>('protocolo-lexpre'),
        getPendencias: dashboard<PendenciasResponse>('pendencias'),
    }
}
