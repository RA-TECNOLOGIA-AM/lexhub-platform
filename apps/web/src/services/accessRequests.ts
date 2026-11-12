import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { DataError } from './errors.ts'
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

// O que o supabase-js devolve num erro de rpc (só o que usamos).
type RpcError = { code?: string; message?: string }

// Erro do banco -> DataError com o status que as telas já entendem.
// 42501 = sem permissão (equipe RA ou sem login); P0001 = regra do pedido (mensagem já em pt-BR);
// PGRST106 = schema api não exposto no Supabase (configuração).
export function toAccessError(error: RpcError): DataError {
    if (error.code === '42501') return new DataError(403, error.message ?? 'Sem permissão.')
    if (error.code === 'P0001') return new DataError(409, error.message ?? 'Não foi possível concluir.')
    if (error.code === 'PGRST106') {
        return new DataError(500, 'O schema "api" não está exposto no Supabase (Settings > API > Exposed schemas).')
    }
    return new DataError(0, 'Não foi possível falar com o servidor. Tente de novo.')
}

// Módulo: os pedidos de acesso pelo Supabase (funções do schema api, sem passar pela API em Python).
// Parâmetro: o cliente do Supabase já logado (o token vai junto e as funções conferem quem chama).
export function createAccessRequestsClient(supabase: SupabaseClient): AccessRequestsClient {
    async function call<T>(fn: string, args?: Record<string, unknown>): Promise<T> {
        const { data, error } = await supabase.schema('api').rpc(fn, args)
        if (error) throw toAccessError(error)
        return data as T
    }

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
