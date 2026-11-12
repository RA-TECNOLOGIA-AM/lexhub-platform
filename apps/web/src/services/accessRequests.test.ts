import { describe, expect, it } from 'vitest'
import type { SupabaseClient } from '@supabase/supabase-js'
import { createAccessRequestsClient } from './accessRequests.ts'
import { toRpcError } from './rpcError.ts'
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

describe('createAccessRequestsClient', () => {
    it('chama a função certa no schema api com os parâmetros certos', async () => {
        const { supabase, calls } = fakeSupabase({ data: { id: 'r1' } })
        const client = createAccessRequestsClient(supabase)
        await client.requestAccess('Escritório X', 'oi')
        await client.listAccessRequests('decided')
        await client.approveAccessRequest('r1', {
            kind: 'existing',
            org_id: 'o1',
            org_role: 'member',
            units: [{ unit_id: 'u1', role_key: 'leitor' }],
        })
        await client.rejectAccessRequest('r2', null)
        expect(calls.map((c) => c.schema)).toEqual(['api', 'api', 'api', 'api'])
        expect(calls[0]).toMatchObject({ fn: 'request_access', args: { p_office: 'Escritório X', p_message: 'oi' } })
        expect(calls[1]).toMatchObject({ fn: 'list_access_requests', args: { p_status: 'decided' } })
        expect(calls[2]).toMatchObject({ fn: 'approve_access_request', args: { p_id: 'r1' } })
        expect(calls[3]).toMatchObject({ fn: 'reject_access_request', args: { p_id: 'r2', p_note: null } })
    })

    it('nunca pediu: getMyAccessRequest devolve null', async () => {
        const { supabase } = fakeSupabase({ data: null })
        expect(await createAccessRequestsClient(supabase).getMyAccessRequest()).toBeNull()
    })

    it('erro do banco vira DataError', async () => {
        const { supabase } = fakeSupabase({ error: { code: 'P0001', message: 'Você já tem um pedido.' } })
        await expect(createAccessRequestsClient(supabase).requestAccess('X', null)).rejects.toEqual(
            new DataError(409, 'Você já tem um pedido.'),
        )
    })
})

describe('toRpcError', () => {
    it('sem permissão = 403, regra = 409, schema não exposto = mensagem de configuração', () => {
        expect(toRpcError({ code: '42501', message: 'Só a equipe RA' }).status).toBe(403)
        expect(toRpcError({ code: 'P0001', message: 'x' }).status).toBe(409)
        expect(toRpcError({ code: 'PGRST106' }).message).toContain('Exposed schemas')
        expect(toRpcError({}).status).toBe(0)
    })
})
