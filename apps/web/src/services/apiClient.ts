import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { createAccessRequestsClient } from './accessRequests.ts'
import { createAccessClient } from './accessClient.ts'
import { createMembersClient } from './membersClient.ts'
import { createSourcesClient } from './sourcesClient.ts'
import { createAuditClient } from './auditClient.ts'
import { createNotificationsClient } from './notifications.ts'
import { DataError } from './errors.ts'
import { toSearch, type Http } from './http.ts'
import type {
    BillingResponse,
    DashboardCatalog,
    DashboardQuery,
    Me,
    Meta,
    PendenciasResponse,
    ProtocoloResponse,
    ClientsResponse,
} from '../types/index.ts'
import { paramsFromQuery } from '../lib/dashboardQuery.ts'

// Módulo: o DataClient de verdade. Login pelo Supabase Auth; todo dado pela API V2.
// Parâmetros: o cliente de login, o http (já com a URL da API e o token) e o endereço do app
// (para onde o Google devolve a pessoa; precisa estar em Redirect URLs no Supabase).
// As rotas seguem o padrão da API: /orgs/{org}/units/{unit}/dashboards/{key}.
// Rota que a API ainda não tem responde 404 (ver apps/api/README.md).
export function createApiClient({
    auth,
    http,
    siteUrl,
}: {
    auth: SupabaseClient
    http: Http
    siteUrl: string
}): DataClient {
    const dashboard =
        <T>(key: string) =>
        (q: { org: string; unit: string; from?: string; to?: string; filters?: object }) =>
            http.get<T>(`/orgs/${q.org}/units/${q.unit}/dashboards/${key}${toSearch(q)}`)

    return {
        // Pedidos de acesso: direto no Supabase (schema api), não pela API em Python.
        ...createAccessRequestsClient(auth),
        // Membros: também direto no Supabase (schema api).
        ...createMembersClient(auth),
        // Acesso: também direto no Supabase (schema api).
        ...createAccessClient(auth),
        // Unidades e fontes: também direto no Supabase (schema api).
        ...createSourcesClient(auth),
        // Auditoria: também direto no Supabase (schema api).
        ...createAuditClient(auth),
        // Notificações do sino: também direto no Supabase (schema api).
        ...createNotificationsClient(auth),

        async signIn(email, password) {
            const { error } = await auth.auth.signInWithPassword({ email: email.trim(), password })
            if (error) {
                // Mesma mensagem do mock: não diz se o e-mail existe.
                throw new DataError(error.status === 400 ? 401 : (error.status ?? 0), 'E-mail ou senha incorretos.')
            }
        },

        // Sai do app: o navegador vai para o Google e volta em /login?code=..., onde o cliente
        // do Supabase troca o código pela sessão sozinho (ver supabase.ts).
        async signInWithGoogle() {
            const { error } = await auth.auth.signInWithOAuth({
                provider: 'google',
                options: { redirectTo: `${siteUrl.replace(/\/+$/, '')}/login` },
            })
            if (error) throw new DataError(error.status ?? 0, 'Não foi possível abrir o login do Google.')
            return 'redirecting'
        },

        async signOut() {
            await auth.auth.signOut()
        },

        async getSessionEmail() {
            const { data } = await auth.auth.getSession()
            return data.session?.user.email ?? null
        },

        getMe: (org) => http.get<Me>(org ? `/me?org=${encodeURIComponent(org)}` : '/me'),
        listDashboards: (org) => http.get<DashboardCatalog>(`/orgs/${org}/dashboards`),
        listFavorites: (org) => http.get<string[]>(`/orgs/${org}/favorites`),
        async setFavorite(org, dashboardKey, favorite) {
            const path = `/orgs/${org}/favorites/${dashboardKey}`
            await (favorite ? http.post(path) : http.delete(path))
        },

        getHubOrder: (org) => http.get<string[]>(`/orgs/${org}/hub-order`),
        async setHubOrder(org, keys) {
            await http.put(`/orgs/${org}/hub-order`, keys)
        },

        listClients: () => http.get<ClientsResponse>('/platform/clients'),
        getBilling: (org) => http.get<BillingResponse>(`/orgs/${org}/billing`),
        getProtocolo: dashboard<ProtocoloResponse>('protocolo-lexpre'),
        getPendencias: dashboard<PendenciasResponse>('pendencias-lexpre'),
        getDashboardData: <T extends { meta: Meta }>(dashboardKey: string, query: DashboardQuery) =>
            dashboard<T>(dashboardKey)(query),

        // Mesmo formato da v1: ?format=xlsx&campos=id_demanda&campos=materia&from=...&materia=ANP
        async exportDashboard({ org, unit, dashboard, format, campos, ...query }) {
            const params = paramsFromQuery(query)
            params.set('format', format)
            for (const campo of campos) params.append('campos', campo)
            const path = `/orgs/${org}/units/${unit}/dashboards/${dashboard}/export?${params}`
            const { blob, filename } = await http.file(path)
            return { blob, filename: filename ?? `${dashboard}_${unit}.${format}` }
        },
    }
}
