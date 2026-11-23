import { describe, expect, it } from 'vitest'
import { fakeSupabase } from './fakeSupabase.ts'
import { createSourcesClient as createSourcesClientWith } from './sourcesClient.ts'
import { DataError } from './errors.ts'
import type { Http } from './http.ts'

// Http falso: guarda os caminhos pedidos e devolve `data`.
function fakeHttp(data: unknown = {}) {
    const paths: string[] = []
    const http = {
        get: async (path: string) => {
            paths.push(path)
            return data
        },
    } as unknown as Http
    return { http, paths }
}

// O cliente com um Http que não deve ser usado (as rotas pelo Supabase).
const createSourcesClient = (supabase: Parameters<typeof createSourcesClientWith>[0]) =>
    createSourcesClientWith(supabase, fakeHttp().http)

describe('createSourcesClient', () => {
    it('listProductOffices busca na API a lista do banco do produto', async () => {
        const offices = { product: 'lexpre', activityLabel: 'x', offices: [] }
        const { http, paths } = fakeHttp(offices)
        const { supabase, calls } = fakeSupabase({ data: {} })
        expect(await createSourcesClientWith(supabase, http).listProductOffices('lexpre')).toEqual(offices)
        expect(paths).toEqual(['/sources/lexpre/offices'])
        expect(calls).toEqual([])
    })

    it('banco e planilha vão para as rotas da API (testar e salvar, testar de novo, senha, desconectar)', async () => {
        const calls: [string, string, unknown][] = []
        const http = {
            get: async (path: string) => (calls.push(['GET', path, undefined]), {}),
            post: async (path: string, body?: unknown) => (calls.push(['POST', path, body]), { tabs: [] }),
            put: async (path: string, body?: unknown) => (calls.push(['PUT', path, body]), {}),
            delete: async (path: string) => (calls.push(['DELETE', path, undefined]), undefined),
        } as unknown as Http
        const { supabase } = fakeSupabase({ data: {} })
        const client = createSourcesClientWith(supabase, http)
        const input = { connector: 'sheets' as const, name: 'F', url: 'https://docs.google.com/x', tab: 'A' }
        await client.getConnectInfo()
        await client.inspectSheet('https://docs.google.com/x')
        await client.connectSource('cliente', 'MC', input)
        await client.retestSource('cliente', 'gs_mc_1')
        await client.changeSourceSecret('cliente', 'gs_mc_1', { url: 'https://docs.google.com/y', writerAck: false })
        await client.disconnectSource('cliente', 'gs_mc_1')
        expect(calls.map(([m, p]) => `${m} ${p}`)).toEqual([
            'GET /sources/connect-info',
            'POST /sources/sheets/inspect',
            'POST /orgs/cliente/units/MC/sources',
            'POST /orgs/cliente/sources/gs_mc_1/test',
            'PUT /orgs/cliente/sources/gs_mc_1/secret',
            'DELETE /orgs/cliente/sources/gs_mc_1',
        ])
        expect(calls[2][2]).toEqual(input)
    })

    it('getSourcesFreshness pede ao cache da API só as fontes da tela e devolve em camelCase', async () => {
        const { http, paths } = fakeHttp({
            sources: {
                lexflow: { fetched_at: '2026-11-23T11:49:00Z', ttl_min: 15, error: null, error_at: null },
            },
        })
        const { supabase, calls } = fakeSupabase({ data: {} })
        const client = createSourcesClientWith(supabase, http)

        expect(await client.getSourcesFreshness('lexgroup', ['lexflow', 'sheets_financeiro_ng'])).toEqual({
            lexflow: { fetchedAt: '2026-11-23T11:49:00Z', cacheMin: 15, error: null, errorAt: null },
        })
        expect(paths).toEqual(['/orgs/lexgroup/sources/freshness?keys=lexflow%2Csheets_financeiro_ng'])
        expect(calls).toEqual([])
    })

    it('getFailingSources pede à API as fontes com falha de cada organização', async () => {
        const { http, paths } = fakeHttp({ orgs: { lexgroup: ['sheets_financeiro_la'] } })
        const { supabase, calls } = fakeSupabase({ data: {} })

        expect(await createSourcesClientWith(supabase, http).getFailingSources()).toEqual({
            lexgroup: ['sheets_financeiro_la'],
        })
        expect(paths).toEqual(['/sources/failing'])
        expect(calls).toEqual([])
    })

    it('linkProductOffice chama api.link_product_office com os nomes do banco', async () => {
        const { supabase, calls } = fakeSupabase({ data: {} })
        await createSourcesClient(supabase).linkProductOffice('cliente', 'C1', 'lexflow', '27')
        expect(calls).toEqual([
            {
                schema: 'api',
                fn: 'link_product_office',
                args: { p_org: 'cliente', p_unit: 'C1', p_product: 'lexflow', p_ref: '27' },
            },
        ])
    })

    it('getSources chama api.list_sources com o slug da organização', async () => {
        const response = { syncEveryMin: 10, unitLimit: null, canManageSources: false, units: [] }
        const { supabase, calls } = fakeSupabase({ data: response })
        expect(await createSourcesClient(supabase).getSources('lexgroup')).toEqual(response)
        expect(calls).toEqual([{ schema: 'api', fn: 'list_sources', args: { p_org: 'lexgroup' } }])
    })

    it('getSourceDetail chama api.source_detail com organização, unidade e fonte', async () => {
        const { supabase, calls } = fakeSupabase({ data: {} })
        await createSourcesClient(supabase).getSourceDetail('lexgroup', 'RJ', 'ng')
        expect(calls).toEqual([
            { schema: 'api', fn: 'source_detail', args: { p_org: 'lexgroup', p_unit: 'RJ', p_source: 'ng' } },
        ])
    })

    it('createUnit e updateUnit mandam os parâmetros com os nomes do banco', async () => {
        const { supabase, calls } = fakeSupabase({ data: {} })
        const client = createSourcesClient(supabase)
        const unit = { code: 'LASP', name: 'Luis Albert SP', timezone: 'America/Sao_Paulo' }
        await client.createUnit('lexgroup', unit)
        await client.updateUnit('lexgroup', unit)
        const args = { p_org: 'lexgroup', p_code: 'LASP', p_name: 'Luis Albert SP', p_timezone: 'America/Sao_Paulo' }
        expect(calls).toEqual([
            { schema: 'api', fn: 'create_unit', args },
            { schema: 'api', fn: 'update_unit', args },
        ])
    })

    it('quem não vê fontes (42501) recebe DataError 403', async () => {
        const { supabase } = fakeSupabase({
            error: { code: '42501', message: 'Você não vê as fontes desta organização.' },
        })
        const error = await createSourcesClient(supabase)
            .getSources('lexgroup')
            .catch((e: unknown) => e)
        expect(error).toBeInstanceOf(DataError)
        expect((error as DataError).status).toBe(403)
    })
})
