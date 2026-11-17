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
