import { describe, expect, it } from 'vitest'
import { DataError } from './errors.ts'
import { createHttp, toSearch } from './http.ts'

type Call = { url: string; init?: RequestInit }

// fetch falso: guarda as chamadas e devolve a resposta pedida.
function fakeFetch(status: number, body: unknown, calls: Call[]) {
    return async (url: string, init?: RequestInit) => {
        calls.push({ url, init })
        return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
    }
}

describe('createHttp', () => {
    it('manda o token no Authorization e junta a URL base', async () => {
        const calls: Call[] = []
        const http = createHttp({
            baseUrl: 'http://api.test/',
            getToken: async () => 'tok',
            fetch: fakeFetch(200, { ok: 1 }, calls),
        })
        expect(await http.get('/health')).toEqual({ ok: 1 })
        expect(calls[0].url).toBe('http://api.test/health')
        expect(new Headers(calls[0].init?.headers).get('Authorization')).toBe('Bearer tok')
    })

    it('sem sessão não manda Authorization', async () => {
        const calls: Call[] = []
        const http = createHttp({
            baseUrl: 'http://api.test',
            getToken: async () => null,
            fetch: fakeFetch(200, {}, calls),
        })
        await http.get('/health')
        expect(new Headers(calls[0].init?.headers).has('Authorization')).toBe(false)
    })

    it('erro HTTP vira DataError com o status e o detail da API', async () => {
        const http = createHttp({
            baseUrl: 'http://api.test',
            getToken: async () => 'tok',
            fetch: fakeFetch(403, { detail: 'Sem acesso' }, []),
        })
        await expect(http.get('/x')).rejects.toEqual(new DataError(403, 'Sem acesso'))
    })

    it('API fora do ar vira DataError 0', async () => {
        const http = createHttp({
            baseUrl: 'http://api.test',
            getToken: async () => null,
            fetch: async () => {
                throw new TypeError('Failed to fetch')
            },
        })
        await expect(http.get('/x')).rejects.toMatchObject({ status: 0 })
    })
})

describe('toSearch', () => {
    it('período e filtros repetidos, sem vazios', () => {
        expect(toSearch({ from: '2026-10-01', to: '2026-10-31', filters: { materia: ['ANP', 'MORA'], uf: [] } })).toBe(
            '?from=2026-10-01&to=2026-10-31&materia=ANP&materia=MORA',
        )
        expect(toSearch({})).toBe('')
    })
})
