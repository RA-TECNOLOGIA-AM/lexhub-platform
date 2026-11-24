import type { DataClient } from './client.ts'
import type { DashboardCatalog, DashboardQuery, Meta } from '../types/index.ts'
import { DataError } from './errors.ts'
import { withEnabled } from '../lib/dashboardSwitch.ts'

type Entry<T> = { at: number; value: Promise<T> }

// Módulo: guarda uma resposta por organização durante `ttlMs`. Erro não fica guardado.
// Parâmetros: validade (ms) e relógio (trocável nos testes). Devolve: get (busca se precisar), set e clear.
export function createOrgMemo<T>(ttlMs: number, now: () => number) {
    const entries = new Map<string, Entry<T>>()
    return {
        get(org: string, load: () => Promise<T>): Promise<T> {
            const hit = entries.get(org)
            if (hit && now() - hit.at < ttlMs) return hit.value
            const entry: Entry<T> = { at: now(), value: load() }
            entries.set(org, entry)
            entry.value.catch(() => {
                if (entries.get(org) === entry) entries.delete(org) // a próxima tentativa vai à API
            })
            return entry.value
        },
        // Depois de uma escrita que deu certo: a tela já mostra o novo valor, sem buscar de novo.
        set(org: string, value: T) {
            entries.set(org, { at: now(), value: Promise.resolve(value) })
        },
        // O valor guardado ainda válido (sem buscar); undefined = não há.
        peek(org: string): Promise<T> | undefined {
            const hit = entries.get(org)
            return hit && now() - hit.at < ttlMs ? hit.value : undefined
        },
        clear() {
            entries.clear()
        },
    }
}

// Módulo: guarda na memória da sessão, por organização, o que o hub pede a cada visita:
// catálogo, favoritos e ordem dos cards. Voltar ao hub não espera a API.
// Parâmetros: o DataClient de verdade, a validade (ms) e o relógio. Devolve: o mesmo DataClient.
// Escritas (estrela, arrastar) vão à API e, se derem certo, atualizam o guardado.
// Segurança: só decide o que a tela mostra; a API confere o acesso em toda rota de dados.
// Entrar ou sair limpa tudo (outra pessoa no mesmo navegador nunca vê o da anterior).
export function withSessionCache(client: DataClient, ttlMs = 5 * 60_000, now: () => number = Date.now): DataClient {
    const catalog = createOrgMemo<DashboardCatalog>(ttlMs, now)
    const favorites = createOrgMemo<string[]>(ttlMs, now)
    const hubOrder = createOrgMemo<string[]>(ttlMs, now)
    const clearAll = () => [catalog, favorites, hubOrder].forEach((m) => m.clear())

    // Um dashboard carregou: o card dele no hub passa a mostrar a mesma hora de atualização
    // (o catálogo guardado pode ser de antes da primeira sincronização e dizer "Atualiza ao abrir").
    async function syncCard(org: string, key: string, syncedAt: string | null) {
        const current = catalog.peek(org)
        if (!current || !syncedAt) return
        const value = await current
        catalog.set(org, {
            ...value,
            available: value.available.map((d) => (d.key === key ? { ...d, synced_at: syncedAt } : d)),
        })
    }
    // Busca os dados de um dashboard e, se deu certo, acerta o card no hub.
    async function withCardSync<T extends { meta: Meta }>(org: string, key: string, load: Promise<T>): Promise<T> {
        const data = await load
        await syncCard(org, key, data.meta.synced_at).catch(() => undefined)
        return data
    }

    const cached: DataClient = {
        ...client,

        getDashboardData: <T extends { meta: Meta }>(key: string, query: DashboardQuery) =>
            withCardSync(query.org, key, client.getDashboardData<T>(key, query)),
        getProtocolo: (query) => withCardSync(query.org, 'protocolo-lexpre', client.getProtocolo(query)),
        getPendencias: (query) => withCardSync(query.org, 'pendencias-lexpre', client.getPendencias(query)),

        listDashboards: (org) => catalog.get(org, () => client.listDashboards(org)),
        listFavorites: (org) => favorites.get(org, () => client.listFavorites(org)),
        getHubOrder: (org) => hubOrder.get(org, () => client.getHubOrder(org)),

        async setFavorite(org, dashboardKey, favorite) {
            await client.setFavorite(org, dashboardKey, favorite)
            const current = favorites.peek(org)
            if (!current) return
            const others = (await current).filter((k) => k !== dashboardKey)
            favorites.set(org, favorite ? [...others, dashboardKey] : others)
        },

        async setDashboardEnabled(org, unit, dashboardKey, enabled) {
            await client.setDashboardEnabled(org, unit, dashboardKey, enabled)
            const current = catalog.peek(org)
            if (current) catalog.set(org, withEnabled(await current, dashboardKey, unit, enabled))
        },

        async setHubOrder(org, keys) {
            await client.setHubOrder(org, keys)
            hubOrder.set(org, keys)
        },

        async signIn(email, password) {
            clearAll()
            await client.signIn(email, password)
        },

        async signInWithGoogle(returnTo) {
            clearAll()
            return client.signInWithGoogle(returnTo)
        },

        async signOut() {
            clearAll()
            await client.signOut()
        },

        async setDeviceSession(session) {
            clearAll()
            await client.setDeviceSession(session)
        },

        // Entrar/sair do modo suporte troca quem a API enxerga: o guardado era de outra visão.
        async startSupport(org, membershipId, reason) {
            const session = await client.startSupport(org, membershipId, reason)
            clearAll()
            return session
        },

        async endSupport(org, sessionId) {
            await client.endSupport(org, sessionId)
            clearAll()
        },
    }

    // A sessão de suporte venceu (409 support_expired): o guardado era da visão do membro. O erro sobe
    // como veio; quem sai do modo e avisa a pessoa é o provider (Tarefa 5).
    const expired = (err: unknown) =>
        err instanceof DataError && err.status === 409 && err.message === 'support_expired'
    const guarded = { ...cached } as Record<string, unknown>
    for (const [name, fn] of Object.entries(cached)) {
        if (typeof fn !== 'function') continue
        guarded[name] = (...args: unknown[]) => {
            const result = (fn as (...a: unknown[]) => unknown).apply(guarded, args)
            if (result instanceof Promise) {
                return result.catch((err: unknown) => {
                    if (expired(err)) clearAll()
                    throw err
                })
            }
            return result
        }
    }
    return guarded as unknown as DataClient
}
