import { DataError } from './errors.ts'
import type { DashboardFilters } from '../types/index.ts'
import { paramsFromQuery } from '../lib/dashboardQuery.ts'

type FetchLike = (url: string, init?: RequestInit) => Promise<Response>

type HttpOptions = {
    baseUrl: string // ex.: http://localhost:8000
    getToken: () => Promise<string | null> // token da sessão (null = sem login)
    fetch?: FetchLike // para os testes; padrão = fetch do navegador
}

// Módulo: as chamadas à API. Parâmetros: URL base e de onde vem o token.
// Esconde: montar a URL, o cabeçalho Authorization e transformar erro HTTP em DataError.
export function createHttp({ baseUrl, getToken, fetch: doFetch = (url, init) => fetch(url, init) }: HttpOptions) {
    const base = baseUrl.replace(/\/+$/, '')

    async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
        const headers = new Headers({ Accept: 'application/json' })
        const token = await getToken()
        if (token) headers.set('Authorization', `Bearer ${token}`)
        if (body !== undefined) headers.set('Content-Type', 'application/json')

        let res: Response
        try {
            res = await doFetch(base + path, {
                method,
                headers,
                body: body === undefined ? undefined : JSON.stringify(body),
            })
        } catch {
            throw new DataError(0, 'Não foi possível falar com a API. Confira a conexão.')
        }
        if (!res.ok) throw new DataError(res.status, await detailOf(res))
        return res.status === 204 ? (undefined as T) : ((await res.json()) as T)
    }

    return {
        get: <T>(path: string) => request<T>('GET', path),
        post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
        put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
        delete: <T>(path: string) => request<T>('DELETE', path),
    }
}

export type Http = ReturnType<typeof createHttp>

// A FastAPI devolve { detail: '...' }; sem isso, uma mensagem pelo status.
async function detailOf(res: Response): Promise<string> {
    try {
        const body = (await res.json()) as { detail?: unknown }
        if (typeof body.detail === 'string') return body.detail
    } catch {
        // corpo vazio ou não-JSON
    }
    return `Erro ${res.status} da API`
}

// Período e filtros na query string, com os nomes da API (?from=&to=&materia=ANP&materia=MORA).
export function toSearch(query: { from?: string; to?: string; filters?: DashboardFilters }): string {
    const text = paramsFromQuery(query).toString()
    return text ? `?${text}` : ''
}
