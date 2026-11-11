import type { DataClient } from './client.ts'
import type { DashboardCatalog } from '../types/index.ts'

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

    return {
        ...client,

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

        async setHubOrder(org, keys) {
            await client.setHubOrder(org, keys)
            hubOrder.set(org, keys)
        },

        async signIn(email, password) {
            clearAll()
            await client.signIn(email, password)
        },

        async signInWithGoogle() {
            clearAll()
            return client.signInWithGoogle()
        },

        async signOut() {
            clearAll()
            await client.signOut()
        },
    }
}
