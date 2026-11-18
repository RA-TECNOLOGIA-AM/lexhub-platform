import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient, DeviceCodeResponse, DeviceSession, DeviceTokenResult } from './client.ts'
import { createAccessRequestsClient } from './accessRequests.ts'
import { createAccessClient } from './accessClient.ts'
import { createMembersClient } from './membersClient.ts'
import { createSourcesClient } from './sourcesClient.ts'
import { createAuditClient } from './auditClient.ts'
import { createBillingClient } from './billingClient.ts'
import { createNotificationsClient } from './notifications.ts'
import { DataError } from './errors.ts'
import { toSearch, type Http } from './http.ts'
import type {
    DashboardCatalog,
    DashboardQuery,
    Me,
    Meta,
    PendenciasResponse,
    ProtocoloResponse,
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
        (q: DashboardQuery) =>
            http.get<T>(`/orgs/${q.org}/units/${q.unit}/dashboards/${key}${toSearch(q)}`, q.signal)

    return {
        // Pedidos de acesso: direto no Supabase (schema api), não pela API em Python.
        ...createAccessRequestsClient(auth),
        // Membros: também direto no Supabase (schema api).
        ...createMembersClient(auth),
        // Acesso: também direto no Supabase (schema api).
        ...createAccessClient(auth),
        // Unidades e fontes: direto no Supabase (schema api); a lista de escritórios vem da API.
        ...createSourcesClient(auth, http),
        // Auditoria: também direto no Supabase (schema api).
        ...createAuditClient(auth),
        // Plano e cobrança e Clientes (plataforma): também direto no Supabase (schema api).
        ...createBillingClient(auth),
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
        async signInWithGoogle(returnTo) {
            const callback = new URL('/login', siteUrl)
            if (returnTo) callback.searchParams.set('returnTo', returnTo)
            const { error } = await auth.auth.signInWithOAuth({
                provider: 'google',
                options: { redirectTo: callback.toString() },
            })
            if (error) throw new DataError(error.status ?? 0, 'Não foi possível abrir o login do Google.')
            return 'redirecting'
        },

        // Só este aparelho: o padrão do Supabase ('global') derrubava também o celular ao sair na TV.
        async signOut() {
            await auth.auth.signOut({ scope: 'local' })
        },
        async signOutOthers() {
            const { error } = await auth.auth.signOut({ scope: 'others' })
            if (error) throw new DataError(error.status ?? 0, 'Não foi possível desconectar os outros aparelhos.')
        },
        // getUser vai ao servidor (getSession só lê o token local, que segue "válido" até vencer).
        async isSessionAlive() {
            const { error } = await auth.auth.getUser()
            if (!error) return true
            return !(error.status === 401 || error.status === 403)
        },

        async getSessionEmail() {
            const { data } = await auth.auth.getSession()
            return data.session?.user.email ?? null
        },

        async getSessionAccessToken() {
            const { data } = await auth.auth.getSession()
            return data.session?.access_token ?? null
        },

        createDeviceCode: () => http.post<DeviceCodeResponse>('/auth/device/code'),
        async pollDeviceToken(deviceCode): Promise<DeviceTokenResult> {
            try {
                const session = await http.get<DeviceSession>(
                    `/auth/device/token?device_code=${encodeURIComponent(deviceCode)}`,
                )
                return { status: 'approved', ...session }
            } catch (error) {
                if (error instanceof DataError) {
                    if (error.code === 'authorization_pending') return { status: 'authorization_pending' }
                    if (error.code === 'slow_down' || error.status === 429) return { status: 'slow_down' }
                    if (error.code === 'expired_token') return { status: 'expired_token' }
                }
                throw error
            }
        },
        async authorizeDevice(userCode) {
            await http.post('/auth/device/authorize', { user_code: userCode })
        },
        async setDeviceSession(session: DeviceSession) {
            const { error } = await auth.auth.setSession({
                access_token: session.access_token,
                refresh_token: session.refresh_token,
            })
            if (error) throw new DataError(error.status ?? 0, 'Não foi possível iniciar a sessão da TV.')
        },

        getMe: (org) => http.get<Me>(org ? `/me?org=${encodeURIComponent(org)}` : '/me'),
        listDashboards: (org) => http.get<DashboardCatalog>(`/orgs/${org}/dashboards`),
        async setDashboardEnabled(org, unit, dashboardKey, enabled) {
            await http.put(`/orgs/${org}/units/${unit}/dashboards/${dashboardKey}/enabled`, { enabled })
        },
        listFavorites: (org) => http.get<string[]>(`/orgs/${org}/favorites`),
        async setFavorite(org, dashboardKey, favorite) {
            const path = `/orgs/${org}/favorites/${dashboardKey}`
            await (favorite ? http.post(path) : http.delete(path))
        },

        getHubOrder: (org) => http.get<string[]>(`/orgs/${org}/hub-order`),
        async setHubOrder(org, keys) {
            await http.put(`/orgs/${org}/hub-order`, keys)
        },

        getProtocolo: dashboard<ProtocoloResponse>('protocolo-lexpre'),
        getPendencias: dashboard<PendenciasResponse>('pendencias-lexpre'),
        getDashboardData: <T extends { meta: Meta }>(dashboardKey: string, query: DashboardQuery) =>
            dashboard<T>(dashboardKey)(query),

        // Mesmo formato da v1: ?format=xlsx&campos=id_demanda&campos=materia&from=...&materia=ANP
        async exportDashboard({ org, unit, dashboard, format, campos, relatorio, opcoes, ...query }) {
            const params = paramsFromQuery(query)
            params.set('format', format)
            for (const campo of campos) params.append('campos', campo)
            if (relatorio) params.set('relatorio', relatorio)
            for (const [chave, valor] of Object.entries(opcoes ?? {})) params.set(chave, valor)
            const path = `/orgs/${org}/units/${unit}/dashboards/${dashboard}/export?${params}`
            const { blob, filename } = await http.file(path)
            return { blob, filename: filename ?? `${dashboard}_${unit}.${format}` }
        },
    }
}
