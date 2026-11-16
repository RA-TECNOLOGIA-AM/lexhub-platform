import { describe, expect, it } from 'vitest'
import { fakeSupabase } from './fakeSupabase.ts'
import { createBillingClient } from './billingClient.ts'
import { DataError } from './errors.ts'

describe('createBillingClient', () => {
    it('getBilling chama api.get_billing com a organização', async () => {
        const billing = { current: { plan: 'pro' }, usage: [], plans: [], invoices: [] }
        const { supabase, calls } = fakeSupabase({ data: billing })
        expect(await createBillingClient(supabase).getBilling('lexgroup')).toEqual(billing)
        expect(calls).toEqual([{ schema: 'api', fn: 'get_billing', args: { p_org: 'lexgroup' } }])
    })

    it('listClients chama api.list_clients sem argumentos', async () => {
        const clients = { clients: [], monthlyRevenue: null }
        const { supabase, calls } = fakeSupabase({ data: clients })
        expect(await createBillingClient(supabase).listClients()).toEqual(clients)
        expect(calls).toEqual([{ schema: 'api', fn: 'list_clients', args: undefined }])
    })

    it('quem não pode ver (42501) recebe DataError 403', async () => {
        const { supabase } = fakeSupabase({
            error: { code: '42501', message: 'Só Owner ou Desenvolvedor veem o plano e a cobrança.' },
        })
        const error = await createBillingClient(supabase)
            .getBilling('lexgroup')
            .catch((e: unknown) => e)
        expect(error).toBeInstanceOf(DataError)
        expect((error as DataError).status).toBe(403)
    })
})
