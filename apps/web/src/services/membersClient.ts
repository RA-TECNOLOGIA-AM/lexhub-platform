import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { createRpc } from './rpc.ts'
import type { InviteResult, Member, MembersResponse } from '../types/index.ts'

type MembersClient = Pick<
    DataClient,
    'listMembers' | 'inviteMembers' | 'setMemberStatus' | 'revokeInvitation' | 'acceptMyInvitations'
>

// Módulo: Membros pelo Supabase (funções do schema api, sem passar pela API em Python).
// Parâmetro: o cliente do Supabase já logado (as funções conferem quem chama e o que ela gere).
export function createMembersClient(supabase: SupabaseClient): MembersClient {
    const call = createRpc(supabase)

    return {
        listMembers: (org) => call<MembersResponse>('list_members', { p_org: org }),
        inviteMembers: (org, invite) =>
            call<InviteResult>('invite_members', {
                p_org: org,
                p_emails: invite.emails,
                p_role: invite.role,
                p_units: invite.units,
                p_teams: invite.teams,
            }),
        setMemberStatus: (org, memberId, status) =>
            call<Member>('set_member_status', { p_org: org, p_member: memberId, p_status: status }),
        async revokeInvitation(id) {
            await call('revoke_invitation', { p_id: id })
        },
        acceptMyInvitations: () => call<number>('accept_my_invitations'),
    }
}
