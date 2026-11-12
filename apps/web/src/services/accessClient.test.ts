import { describe, expect, it } from 'vitest'
import type { SupabaseClient } from '@supabase/supabase-js'
import { createAccessClient } from './accessClient.ts'
import { DataError } from './errors.ts'

// Supabase falso: guarda o schema, a função e os parâmetros de cada rpc e devolve `result`.
function fakeSupabase(result: { data?: unknown; error?: { code?: string; message?: string } }) {
    const calls: { schema: string; fn: string; args: unknown }[] = []
    const supabase = {
        schema: (schema: string) => ({
            rpc: async (fn: string, args?: unknown) => {
                calls.push({ schema, fn, args })
                return { data: result.data ?? null, error: result.error ?? null }
            },
        }),
    } as unknown as SupabaseClient
    return { supabase, calls }
}

describe('createAccessClient', () => {
    it('chama as funções do schema api com os nomes de parâmetro do banco', async () => {
        const { supabase, calls } = fakeSupabase({ data: {} })
        const client = createAccessClient(supabase)
        await client.getAccessOverview('lexgroup', null)
        await client.updateMemberAccess('lexgroup', 'm1', {
            units: [{ code: 'NG', role: 'leitor' }],
            teams: ['t1'],
            org_role: null,
        })
        expect(calls).toEqual([
            { schema: 'api', fn: 'access_overview', args: { p_org: 'lexgroup', p_unit: null } },
            {
                schema: 'api',
                fn: 'update_member_access',
                args: {
                    p_org: 'lexgroup',
                    p_member: 'm1',
                    p_units: [{ code: 'NG', role: 'leitor' }],
                    p_teams: ['t1'],
                    p_org_role: null,
                },
            },
        ])
    })

    it('permissões do menu: my_admin_permissions com o slug', async () => {
        const { supabase, calls } = fakeSupabase({ data: { access: true, members: false } })
        expect(await createAccessClient(supabase).getMyAdminPermissions('lexgroup')).toEqual({
            access: true,
            members: false,
        })
        expect(calls).toEqual([{ schema: 'api', fn: 'my_admin_permissions', args: { p_org: 'lexgroup' } }])
    })

    it('sem permissão no banco (42501) vira DataError 403', async () => {
        const { supabase } = fakeSupabase({
            error: { code: '42501', message: 'Você não gere acesso nesta organização.' },
        })
        const err = await createAccessClient(supabase)
            .getAccessOverview('lexgroup', null)
            .catch((e: unknown) => e)
        expect(err).toBeInstanceOf(DataError)
        expect(err).toMatchObject({ status: 403 })
    })
})
