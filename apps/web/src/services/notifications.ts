import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { createRpc } from './rpc.ts'
import type { NotificationsResponse } from '../types/index.ts'

type NotificationsClient = Pick<DataClient, 'listMyNotifications' | 'markNotificationsRead'>

// Módulo: as notificações do sino pelo Supabase (schema api). O banco filtra por quem está logado.
export function createNotificationsClient(supabase: SupabaseClient): NotificationsClient {
    const call = createRpc(supabase)
    return {
        listMyNotifications: () => call<NotificationsResponse>('list_my_notifications'),
        async markNotificationsRead(ids) {
            await call<number>('mark_notifications_read', { p_ids: ids })
        },
    }
}
