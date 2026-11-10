import type { DataClient } from './client.ts'
import type { DashboardCatalog } from '../types/index.ts'

type Entry = { at: number; value: Promise<DashboardCatalog> }

// Módulo: guarda o catálogo do hub em memória durante a sessão, por organização.
// Parâmetros: o DataClient de verdade, por quanto tempo o catálogo vale (ms) e o relógio (trocável nos testes).
// Devolve: o mesmo DataClient, só com listDashboards em cache. O resto passa direto.
// Por quê: o catálogo muda pouco e cada busca custa uma ida à API; voltar ao hub não precisa esperar.
// Segurança: o cache só decide o que a tela mostra; a API confere o acesso de novo em toda rota de dashboard.
// Entrar ou sair limpa tudo (outra pessoa no mesmo navegador nunca vê o catálogo da anterior).
export function withCatalogCache(client: DataClient, ttlMs = 5 * 60_000, now: () => number = Date.now): DataClient {
    const cache = new Map<string, Entry>()

    return {
        ...client,

        listDashboards(org) {
            const hit = cache.get(org)
            if (hit && now() - hit.at < ttlMs) return hit.value
            const entry: Entry = { at: now(), value: client.listDashboards(org) }
            cache.set(org, entry)
            // Erro não fica guardado: a próxima tentativa vai à API de novo.
            entry.value.catch(() => {
                if (cache.get(org) === entry) cache.delete(org)
            })
            return entry.value
        },

        async signIn(email, password) {
            cache.clear()
            await client.signIn(email, password)
        },

        async signOut() {
            cache.clear()
            await client.signOut()
        },
    }
}
