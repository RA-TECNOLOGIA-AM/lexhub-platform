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

    // O caminho comum de toda chamada: token, envio e erro HTTP -> DataError. Devolve a resposta crua.
    async function send(method: string, path: string, body?: unknown, accept = 'application/json'): Promise<Response> {
        const headers = new Headers({ Accept: accept })
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
        if (!res.ok) throw await errorOf(res)
        return res
    }

    // JSON: quase todas as rotas.
    async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
        const res = await send(method, path, body)
        return res.status === 204 ? (undefined as T) : ((await res.json()) as T)
    }

    // Arquivo (exportação): o conteúdo e o nome que o servidor mandou (null = não mandou nome).
    async function file(path: string): Promise<{ blob: Blob; filename: string | null }> {
        const res = await send('GET', path, undefined, '*/*')
        return { blob: await res.blob(), filename: filenameOf(res.headers.get('Content-Disposition')) }
    }

    return {
        get: <T>(path: string) => request<T>('GET', path),
        post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
        put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
        delete: <T>(path: string) => request<T>('DELETE', path),
        file,
    }
}

export type Http = ReturnType<typeof createHttp>

// FastAPI devolve { detail }; erros OAuth seguem { error, error_description }.
async function errorOf(res: Response): Promise<DataError> {
    try {
        const body = (await res.json()) as {
            detail?: unknown
            error?: unknown
            error_description?: unknown
        }
        if (typeof body.error === 'string') {
            const message =
                typeof body.error_description === 'string' ? body.error_description : `Erro ${res.status} da API`
            return new DataError(res.status, message, body.error)
        }
        if (typeof body.detail === 'string') return new DataError(res.status, body.detail)
    } catch {
        // corpo vazio ou não-JSON
    }
    return new DataError(res.status, `Erro ${res.status} da API`)
}

// 'attachment; filename="protocolo.xlsx"' -> 'protocolo.xlsx' (também o formato filename*=UTF-8''...).
function filenameOf(header: string | null): string | null {
    const match = header?.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i)
    return match ? decodeURIComponent(match[1]) : null
}

// Período e filtros na query string, com os nomes da API (?from=&to=&materia=ANP&materia=MORA).
export function toSearch(query: { from?: string; to?: string; filters?: DashboardFilters }): string {
    const text = paramsFromQuery(query).toString()
    return text ? `?${text}` : ''
}
