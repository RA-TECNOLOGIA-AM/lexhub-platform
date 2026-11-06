import type { DataClient } from './client.ts'
import { DataError } from './errors.ts'
import { catalog, me, pendencias, protocolo, testUsers} from './mock-data.ts'

// Simula a rede: um pouco de espera faz o "carregando" aparecer de verdade.
const LATENCY_MS = 300
const wait = () => new Promise((resolve) => setTimeout(resolve, LATENCY_MS))

// Devolve uma cópia: assim uma tela que altere o objeto não estraga o mock das outras.
const copy = <T>(value: T): T => structuredClone(value)

// Sessão fictícia: fica no sessionStorage (sobrevive ao F5, some ao fechar a aba).
const SESSION_KEY = 'lexhub.mock.session'

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

export function createMockClient(): DataClient {
    return {
           // Confere contra os usuários de teste do mock-data.ts (o Supabase fará isso de verdade).
        async signIn(email, password) {
            await wait()
            const ok = testUsers.some(
                (u) => u.email === email.trim().toLowerCase() && u.password === password,
            )
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

        async getProtocolo(query) {
            await wait()
            requireSession()
            checkAccess('protocolo-lexpre', query.unit)
            const meta = { ...protocolo.meta, unit: query.unit, from: query.from ?? protocolo.meta.from, to: query.to ?? protocolo.meta.to }
            return copy({ ...protocolo, meta })
        },

        async getPendencias(query) {
            await wait()
            requireSession()
            checkAccess('pendencias', query.unit)
            const meta = { ...pendencias.meta, unit: query.unit, from: query.from ?? pendencias.meta.from, to: query.to ?? pendencias.meta.to }
            return copy({ ...pendencias, meta })
        },
    }
}