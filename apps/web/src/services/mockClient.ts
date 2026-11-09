import type { DataClient } from './client.ts'
import { DataError } from './errors.ts'
import {
    access,
    audit,
    billingFor,
    catalog,
    clients,
    createMembersStore,
    defaultFavorites,
    me,
    pendenciasFor,
    protocoloFor,
    testUsers,
} from './mock/index.ts'
import type { DashboardQuery, Meta } from '../types/index.ts'

// Simula a rede: um pouco de espera faz o "carregando" aparecer de verdade.
const LATENCY_MS = 300
const wait = () => new Promise((resolve) => setTimeout(resolve, LATENCY_MS))

// Devolve uma cópia: assim uma tela que altere o objeto não estraga o mock das outras.
const copy = <T>(value: T): T => structuredClone(value)

// Sessão fictícia: fica no sessionStorage (sobrevive ao F5, some ao fechar a aba).
const SESSION_KEY = 'lexhub.mock.session'

// Favoritos: ficam no localStorage (sobrevivem a fechar a aba, como na API ficarão no banco).
const FAVORITES_KEY = 'lexhub.mock.favorites'

// Membros do mock: a lista muda com os convites (volta ao original no F5).
const memberStore = createMembersStore(me.user.name)

function requireSession() {
    if (sessionStorage.getItem(SESSION_KEY) === null) {
        throw new DataError(401, 'Sessão expirada ou inexistente')
    }
}

// Mesma regra da API: dashboard fora das unidades liberadas = 403.
function checkAccess(dashboardKey: string, unit: string) {
    const dash = catalog.available.find((d) => d.key === dashboardKey)
    if (!dash || !dash.units.includes(unit)) {
        throw new DataError(403, 'Você não tem acesso a este dashboard nesta unidade')
    }
}

// Módulo: o caminho de toda resposta de dashboard no mock (como a API fará):
// espera, confere sessão (401) e acesso (403), monta os dados da unidade e aplica o período.
// Parâmetros: a key do dashboard, a consulta e a função que monta os dados de uma unidade.
async function dashboardResponse<T extends { meta: Meta }>(
    dashboardKey: string,
    query: DashboardQuery,
    build: (unit: string, query: DashboardQuery) => T,
): Promise<T> {
    await wait()
    requireSession()
    checkAccess(dashboardKey, query.unit)
    const data = build(query.unit, query)
    data.meta.from = query.from ?? data.meta.from
    data.meta.to = query.to ?? data.meta.to
    return data
}

export function createMockClient(): DataClient {
    return {
        // Confere contra os usuários de teste de mock/users.ts (o Supabase fará isso de verdade).
        async signIn(email, password) {
            await wait()
            const ok = testUsers.some((u) => u.email === email.trim().toLowerCase() && u.password === password)
            if (!ok) {
                throw new DataError(401, 'E-mail ou senha incorretos.')
            }
            sessionStorage.setItem(SESSION_KEY, email)
        },

        async signOut() {
            sessionStorage.removeItem(SESSION_KEY)
        },

        async getMe() {
            await wait()
            requireSession()
            return copy(me)
        },

        async listDashboards() {
            await wait()
            requireSession()
            return copy(catalog)
        },

        async listMembers() {
            await wait()
            requireSession()
            return memberStore.list()
        },

        async inviteMembers(_org, invite) {
            await wait()
            requireSession()
            memberStore.invite(invite)
        },

        async listFavorites() {
            await wait()
            requireSession()
            const saved = localStorage.getItem(FAVORITES_KEY)
            return saved ? (JSON.parse(saved) as string[]) : [...defaultFavorites]
        },

        async setFavorite(org, dashboardKey, favorite) {
            const current = await this.listFavorites(org)
            const next = favorite ? [...new Set([...current, dashboardKey])] : current.filter((k) => k !== dashboardKey)
            localStorage.setItem(FAVORITES_KEY, JSON.stringify(next))
        },

        // Assentos lidos de Membros: convidar alguém muda o número aqui também.
        async getBilling() {
            await wait()
            requireSession()
            return billingFor(memberStore.list().seats)
        },

        async getAccess() {
            await wait()
            requireSession()
            return copy(access)
        },

        async getAudit() {
            await wait()
            requireSession()
            return copy(audit)
        },

        // Mesma regra da API: só a equipe RA (platformStaff) vê os clientes.
        async listClients() {
            await wait()
            requireSession()
            if (!me.user.platformStaff) throw new DataError(403, 'Só a equipe RA Tecnologia vê os clientes')
            return copy(clients)
        },

        getProtocolo: (query) => dashboardResponse('protocolo-lexpre', query, protocoloFor),
        getPendencias: (query) => dashboardResponse('pendencias', query, pendenciasFor),
    }
}
