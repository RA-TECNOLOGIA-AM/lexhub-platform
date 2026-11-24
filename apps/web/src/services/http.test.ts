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

    it('getHeaders vai em toda chamada e é lido a cada uma', async () => {
        const calls: Call[] = []
        let id = 'a'
        const http = createHttp({
            baseUrl: 'http://api.test',
            getToken: async () => 'tok',
            getHeaders: () => ({ 'X-Support-Session': id }),
            fetch: fakeFetch(200, {}, calls),
        })
        await http.get('/x')
        id = 'b'
        await http.post('/y', {})
        expect(new Headers(calls[0].init?.headers).get('X-Support-Session')).toBe('a')
        expect(new Headers(calls[1].init?.headers).get('X-Support-Session')).toBe('b')
    })

    it('sem getHeaders não manda cabeçalho extra', async () => {
        const calls: Call[] = []
        const http = createHttp({
            baseUrl: 'http://api.test',
            getToken: async () => 'tok',
            fetch: fakeFetch(200, {}, calls),
        })
        await http.get('/x')
        expect(new Headers(calls[0].init?.headers).has('X-Support-Session')).toBe(false)
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

    it('preserva o código e a descrição de erros OAuth', async () => {
        const http = createHttp({
            baseUrl: 'http://api.test',
            getToken: async () => 'tok',
            fetch: fakeFetch(400, { error: 'authorization_pending', error_description: 'Aguardando aprovação.' }, []),
        })
        await expect(http.get('/x')).rejects.toEqual(
            new DataError(400, 'Aguardando aprovação.', 'authorization_pending'),
        )
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

describe('http.file', () => {
    const fileFetch = (headers: Record<string, string>) => async () => new Response('a;b', { status: 200, headers })

    it('devolve o conteúdo e o nome do Content-Disposition', async () => {
        const http = createHttp({
            baseUrl: 'http://api',
            getToken: async () => 't',
            fetch: fileFetch({ 'Content-Disposition': 'attachment; filename="protocolo_NG.xlsx"' }),
        })
        const { blob, filename } = await http.file('/x')
        expect(filename).toBe('protocolo_NG.xlsx')
        expect(await blob.text()).toBe('a;b')
    })

    it('sem Content-Disposition, o nome vem null (quem chama escolhe um)', async () => {
        const http = createHttp({ baseUrl: 'http://api', getToken: async () => null, fetch: fileFetch({}) })
        expect((await http.file('/x')).filename).toBeNull()
    })
})

describe('createHttp: cancelamento', () => {
    it('repassa o signal ao fetch', async () => {
        const calls: Call[] = []
        const http = createHttp({
            baseUrl: 'http://api.test',
            getToken: async () => null,
            fetch: fakeFetch(200, {}, calls),
        })
        const controller = new AbortController()
        await http.get('/x', controller.signal)
        expect(calls[0].init?.signal).toBe(controller.signal)
    })

    it('busca cancelada sobe o erro do cancelamento, não "sem conexão"', async () => {
        const controller = new AbortController()
        const http = createHttp({
            baseUrl: 'http://api.test',
            getToken: async () => null,
            fetch: async (_url, init) => {
                controller.abort()
                throw init?.signal?.reason
            },
        })
        const err = await http.get('/x', controller.signal).catch((e: unknown) => e)
        expect(err).not.toBeInstanceOf(DataError)
        expect((err as DOMException).name).toBe('AbortError')
    })

    it('falha de rede sem cancelamento continua virando DataError 0', async () => {
        const http = createHttp({
            baseUrl: 'http://api.test',
            getToken: async () => null,
            fetch: async () => {
                throw new TypeError('Failed to fetch')
            },
        })
        const err = await http.get('/x', new AbortController().signal).catch((e: unknown) => e)
        expect(err).toBeInstanceOf(DataError)
        expect((err as DataError).status).toBe(0)
    })
})
