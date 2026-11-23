import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { createRpc } from './rpc.ts'
import { actionFilter, toAuditEvent } from './auditEvents.ts'
import type { AuditResponse, RawAuditEvent } from '../types/index.ts'

type AuditClient = Pick<DataClient, 'getAudit' | 'logAuditExport' | 'logDashboardView'>

// Módulo: Auditoria pelo Supabase (api.list_audit, sem a API em Python). O banco devolve o evento cru;
// auditEvents.ts monta o texto da tela. Só Owner/Desenvolvedor veem (o banco recusa os outros com 403).
export function createAuditClient(supabase: SupabaseClient): AuditClient {
    const call = createRpc(supabase)
    return {
        // Período, tipo e pessoa vão para o banco: a resposta já vem filtrada (até 2000 eventos), com a lista de
        // pessoas do período (para o campo Pessoa). Banco antigo sem truncated/actors: false / [].
        async getAudit(org, query) {
            const res = await call<{
                events: RawAuditEvent[]
                truncated?: boolean
                actors?: string[]
                units?: AuditResponse['units']
                orgs?: AuditResponse['orgs']
            }>('list_audit', {
                p_org: org,
                p_from: query.from,
                p_to: query.to,
                ...actionFilter(query.kind),
                p_actor: query.actor || null,
                p_unit: query.unit || null,
            })
            return {
                events: res.events.map(toAuditEvent),
                truncated: res.truncated ?? false,
                actors: res.actors ?? [],
                units: res.units ?? [],
                orgs: res.orgs ?? null,
            }
        },
        // Abriu um dashboard: o banco ignora repetição da mesma pessoa/dashboard/unidade em menos de 5 min.
        async logDashboardView(org, unit, dashboardKey) {
            await call<boolean>('log_dashboard_view', { p_org: org, p_unit: unit, p_dashboard: dashboardKey })
        },
        async logAuditExport(org, filter, rows) {
            await call<null>('log_audit_export', {
                p_org: org,
                p_kind: filter.kind,
                p_actor: filter.actor,
                p_rows: rows,
                p_unit: filter.unit || null,
            })
        },
    }
}
