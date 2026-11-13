import { describe, expect, it } from 'vitest'
import { fakeSupabase } from './fakeSupabase.ts'
import { createMembersClient } from './membersClient.ts'
import { DataError } from './errors.ts'

describe('createMembersClient', () => {
    it('convite: chama invite_members no schema api com os parâmetros do banco', async () => {
        const { supabase, calls } = fakeSupabase({ data: { invited: ['a@x.com'], skipped: [] } })
        const result = await createMembersClient(supabase).inviteMembers('lexgroup', {
            emails: ['a@x.com'],
            role: 'leitor',
            units: ['NG'],
            teams: [],
        })
        expect(calls).toEqual([
            {
                schema: 'api',
                fn: 'invite_members',
                args: { p_org: 'lexgroup', p_emails: ['a@x.com'], p_role: 'leitor', p_units: ['NG'], p_teams: [] },
            },
        ])
        expect(result).toEqual({ invited: ['a@x.com'], skipped: [] })
    })

    it('lista, situação, cancelar e aceitar usam as funções e os nomes de parâmetro do banco', async () => {
        const { supabase, calls } = fakeSupabase({ data: 0 })
        const client = createMembersClient(supabase)
        await client.listMembers('lexgroup')
        await client.setMemberStatus('lexgroup', 'm1', 'disabled')
        await client.revokeInvitation('i1')
        await client.acceptMyInvitations()
        expect(calls.map(({ fn, args }) => ({ fn, args }))).toEqual([
            { fn: 'list_members', args: { p_org: 'lexgroup' } },
            { fn: 'set_member_status', args: { p_org: 'lexgroup', p_member: 'm1', p_status: 'disabled' } },
            { fn: 'revoke_invitation', args: { p_id: 'i1' } },
            { fn: 'accept_my_invitations', args: undefined },
        ])
    })

    it('sem permissão no banco (42501) vira DataError 403 com a mensagem do banco', async () => {
        const { supabase } = fakeSupabase({
            error: { code: '42501', message: 'Você não gere membros nesta organização.' },
        })
        const err = await createMembersClient(supabase)
            .listMembers('lexgroup')
            .catch((e: unknown) => e)
        expect(err).toBeInstanceOf(DataError)
        expect(err).toMatchObject({ status: 403, message: 'Você não gere membros nesta organização.' })
    })
})
