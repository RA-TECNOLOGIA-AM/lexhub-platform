import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { createRpc } from './rpc.ts'
import type { AccessOverview, AdminPermissions, Member } from '../types/index.ts'

type AccessClient = Pick<DataClient, 'getAccessOverview' | 'updateMemberAccess' | 'getMyAdminPermissions'>

// Módulo: Acesso pelo Supabase (funções do schema api, sem passar pela API em Python).
// Parâmetro: o cliente do Supabase já logado (as funções conferem o que quem chama gere).
export function createAccessClient(supabase: SupabaseClient): AccessClient {
    const call = createRpc(supabase)

    return {
        getMyAdminPermissions: (org) => call<AdminPermissions>('my_admin_permissions', { p_org: org }),
        getAccessOverview: (org, unit) => call<AccessOverview>('access_overview', { p_org: org, p_unit: unit }),
        updateMemberAccess: (org, memberId, update) =>
            call<Member>('update_member_access', {
                p_org: org,
                p_member: memberId,
                p_units: update.units,
                p_teams: update.teams,
                p_org_role: update.org_role,
            }),
    }
}
