import { describe, expect, it } from 'vitest'
import { fakeSupabase } from './fakeSupabase.ts'
import { createSourcesClient } from './sourcesClient.ts'
import { DataError } from './errors.ts'

describe('createSourcesClient', () => {
    it('getSources chama api.list_sources com o slug da organização', async () => {
        const response = { syncEveryMin: 10, unitLimit: null, units: [] }
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
