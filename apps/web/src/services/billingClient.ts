import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { createRpc } from './rpc.ts'
import type { BillingResponse, ClientsResponse, OrgClosureImpact } from '../types/index.ts'

type BillingClient = Pick<
    DataClient,
    'getBilling' | 'listClients' | 'getOrgClosureImpact' | 'closeOrganization' | 'reopenOrganization'
>

// Módulo: Plano e cobrança e Clientes (plataforma) pelo Supabase (schema api, sem a API em Python).
// O banco já devolve no formato das telas. Quem não pode ver recebe 403 (42501):
// cobrança = Owner/Desenvolvedor ou equipe RA; clientes = Owner/Desenvolvedor da LexGroup ou equipe RA.
export function createBillingClient(supabase: SupabaseClient): BillingClient {
    const call = createRpc(supabase)
    return {
        getBilling: (org) => call<BillingResponse>('get_billing', { p_org: org }),
        listClients: () => call<ClientsResponse>('list_clients'),
        getOrgClosureImpact: (org) => call<OrgClosureImpact>('org_closure_impact', { p_org: org }),
        reopenOrganization: async (org) => {
            await call<null>('reopen_organization', { p_org: org })
        },
        closeOrganization: async (org, confirmName) => {
            await call<null>('close_organization', { p_org: org, p_confirm: confirmName })
        },
    }
}
