import { describe, expect, it } from 'vitest'
import { fakeSupabase } from './fakeSupabase.ts'
import { createAuditClient } from './auditClient.ts'
import { DataError } from './errors.ts'
import type { AuditQuery } from '../types/index.ts'

const ALL: AuditQuery = { from: null, to: null, kind: '', actor: '' }

describe('createAuditClient', () => {
    it('chama api.list_audit e traduz cada evento', async () => {
        const { supabase, calls } = fakeSupabase({
            data: {
                events: [
                    {
                        id: '7',
                        at: '2026-11-13T10:00:00-04:00',
                        action: 'member.disabled',
                        actor: 'Ana Ribeiro',
                        actorEmail: 'ana@lexgroup.com.br',
                        targetType: 'membership',
                        targetId: 'm1',
                        targetName: 'Bruno Melo',
                        metadata: { email: 'bruno@lexgroup.com.br' },
                    },
                ],
            },
        })
        const { events, truncated, actors } = await createAuditClient(supabase).getAudit('lexgroup', ALL)
        expect(actors).toEqual([]) // banco antigo sem 'actors': lista vazia
        expect(calls).toEqual([
            {
                schema: 'api',
                fn: 'list_audit',
                args: {
                    p_org: 'lexgroup',
                    p_from: null,
                    p_to: null,
                    p_actions: null,
                    p_exclude_actions: null,
                    p_actor: null,
                },
            },
        ])
        expect(truncated).toBe(false)
        expect(events).toEqual([
            {
                id: '7',
                at: '2026-11-13T10:00:00-04:00',
                actor: 'Ana Ribeiro',
                email: 'ana@lexgroup.com.br',
                kind: 'access',
                action: 'Desativou membro',
                detail: 'bruno@lexgroup.com.br',
            },
        ])
    })

    it('quem não é Owner/Desenvolvedor (42501) recebe DataError 403', async () => {
        const { supabase } = fakeSupabase({
            error: { code: '42501', message: 'Só Owner ou Desenvolvedor veem a auditoria.' },
        })
        const error = await createAuditClient(supabase)
            .getAudit('lexgroup', ALL)
            .catch((e: unknown) => e)
        expect(error).toBeInstanceOf(DataError)
        expect((error as DataError).status).toBe(403)
    })

    it('manda período e os eventos do tipo, e repassa o aviso de limite', async () => {
        const { supabase, calls } = fakeSupabase({ data: { events: [], truncated: true } })
        const { supabase: s2 } = fakeSupabase({ data: { events: [], truncated: true, actors: ['Ana Ribeiro'] } })
        const query: AuditQuery = {
            from: '2026-11-12T00:00:00-04:00',
            to: '2026-11-20T00:00:00-04:00',
            kind: 'view',
            actor: 'Ana Ribeiro',
        }
        await createAuditClient(supabase).getAudit('lexgroup', query)
        expect(calls[0]?.args).toEqual({
            p_org: 'lexgroup',
            p_from: '2026-11-12T00:00:00-04:00',
            p_to: '2026-11-20T00:00:00-04:00',
            p_actions: ['dashboard.view'],
            p_exclude_actions: null,
            p_actor: 'Ana Ribeiro',
        })
        const { truncated, actors } = await createAuditClient(s2).getAudit('lexgroup', query)
        expect(truncated).toBe(true)
        expect(actors).toEqual(['Ana Ribeiro'])
    })

    it('registra a abertura de um dashboard', async () => {
        const { supabase, calls } = fakeSupabase({ data: true })
        await createAuditClient(supabase).logDashboardView('lexgroup', 'NG', 'comercial-lexpre')
        expect(calls).toEqual([
            {
                schema: 'api',
                fn: 'log_dashboard_view',
                args: { p_org: 'lexgroup', p_unit: 'NG', p_dashboard: 'comercial-lexpre' },
            },
        ])
    })
})
