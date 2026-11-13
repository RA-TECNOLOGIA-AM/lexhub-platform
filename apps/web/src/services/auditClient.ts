import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { createRpc } from './rpc.ts'
import { toAuditEvent } from './auditEvents.ts'
import type { RawAuditEvent } from '../types/index.ts'

type AuditClient = Pick<DataClient, 'getAudit'>

// Módulo: Auditoria pelo Supabase (api.list_audit, sem a API em Python). O banco devolve o evento cru;
// auditEvents.ts monta o texto da tela. Só Owner/Desenvolvedor veem (o banco recusa os outros com 403).
export function createAuditClient(supabase: SupabaseClient): AuditClient {
    const call = createRpc(supabase)
    return {
        async getAudit(org) {
            const { events } = await call<{ events: RawAuditEvent[] }>('list_audit', { p_org: org })
            return { events: events.map(toAuditEvent) }
        },
    }
}
