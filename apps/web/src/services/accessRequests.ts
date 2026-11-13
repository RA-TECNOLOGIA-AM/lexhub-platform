import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { createRpc } from './rpc.ts'
import type { AccessRequest, ApprovalOrg } from '../types/index.ts'

type AccessRequestsClient = Pick<
    DataClient,
    | 'requestAccess'
    | 'getMyAccessRequest'
    | 'countPendingAccessRequests'
    | 'listAccessRequests'
    | 'getApprovalOptions'
    | 'approveAccessRequest'
    | 'rejectAccessRequest'
>

// Módulo: os pedidos de acesso pelo Supabase (funções do schema api, sem passar pela API em Python).
// Parâmetro: o cliente do Supabase já logado (o token vai junto e as funções conferem quem chama).
export function createAccessRequestsClient(supabase: SupabaseClient): AccessRequestsClient {
    const call = createRpc(supabase)

    return {
        requestAccess: (office, message) =>
            call<AccessRequest>('request_access', { p_office: office, p_message: message }),
        getMyAccessRequest: async () => (await call<AccessRequest | null>('my_access_request')) ?? null,
        countPendingAccessRequests: () => call<number>('count_pending_access_requests'),
        listAccessRequests: (status) => call<AccessRequest[]>('list_access_requests', { p_status: status }),
        getApprovalOptions: () => call<ApprovalOrg[]>('approval_options'),
        approveAccessRequest: (id, target) =>
            call<AccessRequest>('approve_access_request', { p_id: id, p_target: target }),
        rejectAccessRequest: (id, note) => call<AccessRequest>('reject_access_request', { p_id: id, p_note: note }),
    }
}
