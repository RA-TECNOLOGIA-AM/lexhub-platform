import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { createRpc } from './rpc.ts'
import type { AccountSession } from '../types/index.ts'

type DevicesClient = Pick<DataClient, 'listMySessions' | 'revokeMySession'>

type Row = {
    id: string
    created_at: string
    last_active_at: string
    user_agent: string | null
    ip: string | null
    current: boolean
}

// Módulo: Dispositivos pelo Supabase (api.list_my_sessions / api.revoke_my_session).
// Parâmetro: o cliente do Supabase já logado (as funções só enxergam as sessões de quem chama).
export function createDevicesClient(supabase: SupabaseClient): DevicesClient {
    const call = createRpc(supabase)

    return {
        async listMySessions(): Promise<AccountSession[]> {
            const rows = await call<Row[]>('list_my_sessions')
            return (rows ?? []).map((r) => ({
                id: r.id,
                createdAt: r.created_at,
                lastActiveAt: r.last_active_at,
                userAgent: r.user_agent,
                ip: r.ip,
                current: r.current,
            }))
        },
        async revokeMySession(id) {
            await call('revoke_my_session', { p_id: id })
        },
    }
}
