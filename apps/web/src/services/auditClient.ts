import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { createRpc } from './rpc.ts'
import { toAuditEvent } from './auditEvents.ts'
import type { RawAuditEvent } from '../types/index.ts'

type AuditClient = Pick<DataClient, 'getAudit' | 'logAuditExport'>

// Módulo: Auditoria pelo Supabase (api.list_audit, sem a API em Python). O banco devolve o evento cru;
// auditEvents.ts monta o texto da tela. Só Owner/Desenvolvedor veem (o banco recusa os outros com 403).
export function createAuditClient(supabase: SupabaseClient): AuditClient {
    const call = createRpc(supabase)
    return {
        async getAudit(org) {
            const { events } = await call<{ events: RawAuditEvent[] }>('list_audit', { p_org: org })
            return { events: events.map(toAuditEvent) }
        },
        async logAuditExport(org, filter, rows) {
            await call<null>('log_audit_export', {
                p_org: org,
                p_kind: filter.kind,
                p_actor: filter.actor,
                p_rows: rows,
            })
        },
    }
}
