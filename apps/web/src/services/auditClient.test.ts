import { describe, expect, it } from 'vitest'
import { fakeSupabase } from './fakeSupabase.ts'
import { createAuditClient } from './auditClient.ts'
import { DataError } from './errors.ts'

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
                        targetType: 'membership',
                        targetId: 'm1',
                        targetName: 'Bruno Melo',
                        metadata: { email: 'bruno@lexgroup.com.br' },
                    },
                ],
            },
        })
        const { events } = await createAuditClient(supabase).getAudit('lexgroup')
        expect(calls).toEqual([{ schema: 'api', fn: 'list_audit', args: { p_org: 'lexgroup' } }])
        expect(events).toEqual([
            {
                id: '7',
                at: '2026-11-13T10:00:00-04:00',
                actor: 'Ana Ribeiro',
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
            .getAudit('lexgroup')
            .catch((e: unknown) => e)
        expect(error).toBeInstanceOf(DataError)
        expect((error as DataError).status).toBe(403)
    })
})
