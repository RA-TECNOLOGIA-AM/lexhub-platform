import { DataError } from '../errors.ts'
import type {
    InviteRequest,
    InviteResult,
    Invitation,
    Member,
    MemberAccessUpdate,
    MembersResponse,
} from '../../types/index.ts'

const DAY = 24 * 60 * 60 * 1000
const daysFromNow = (days: number) => new Date(Date.now() + days * DAY).toISOString()

// Os membros do protótipo, no formato de api.list_members (cargo por unidade).
// O mock é Owner/Desenvolvedor: gere todas as unidades e pode convidar Desenvolvedor.
export const members: MembersResponse = {
    units: [
        { code: 'LA_AM', name: 'Luis Albert AM' },
        { code: 'LA_RJ', name: 'Luis Albert RJ' },
        { code: 'NG', name: 'Nicolas Gomes' },
    ],
    teams: [
        { id: 't-comercial', name: 'Comercial', unit: 'LA_AM' },
        { id: 't-protocolo', name: 'Protocolo', unit: 'LA_RJ' },
        { id: 't-diretoria', name: 'Diretoria', unit: 'NG' },
        { id: 't-pendencias', name: 'Pendências', unit: 'NG' },
    ],
    can_invite_admin: true,
    members: [
        {
            id: 'm1',
            name: 'Ana Ribeiro',
            email: 'ana@lexgroup.com.br',
            org_role: 'admin',
            units: [],
            teams: ['Diretoria'],
            team_ids: ['t-diretoria'],
            status: 'active',
            last_seen_at: daysFromNow(0),
            security: 'Google',
        },
        {
            id: 'm2',
            name: 'Bruno Melo',
            email: 'bruno@lexgroup.com.br',
            org_role: 'member',
            units: [
                { code: 'LA_AM', role: 'controller' },
                { code: 'NG', role: 'gestor' },
            ],
            teams: ['Comercial'],
            team_ids: ['t-comercial'],
            status: 'active',
            last_seen_at: daysFromNow(-1),
            security: 'Google',
        },
        {
            id: 'm3',
            name: 'Carla Souza',
            email: 'carla@lexgroup.com.br',
            org_role: 'member',
            units: [{ code: 'LA_RJ', role: 'colaborador' }],
            teams: ['Protocolo'],
            team_ids: ['t-protocolo'],
            status: 'active',
            last_seen_at: daysFromNow(-2),
            security: 'Google',
        },
        {
            id: 'm4',
            name: 'Diego Pires',
            email: 'diego@lexgroup.com.br',
            org_role: 'member',
            units: [{ code: 'NG', role: 'colaborador' }],
            teams: ['Pendências'],
            team_ids: ['t-pendencias'],
            status: 'active',
            last_seen_at: null,
            security: null,
        },
        {
            id: 'm5',
            name: 'Fernanda Lopes',
            email: 'fernanda@lexgroup.com.br',
            org_role: 'member',
            units: [{ code: 'NG', role: 'leitor' }],
            teams: ['Diretoria'],
            team_ids: ['t-diretoria'],
            status: 'disabled',
            last_seen_at: daysFromNow(-40),
            security: 'Google',
        },
    ],
    invitations: [
        {
            id: 'i1',
            email: 'gabriel@lexgroup.com.br',
            role: 'colaborador',
            units: ['NG'],
            teams: ['Pendências'],
            invited_by: 'Ana Ribeiro',
            created_at: daysFromNow(-2),
            expires_at: daysFromNow(5),
        },
    ],
}

// Módulo: os membros do mock como um "banco" em memória (volta ao original no F5).
// Parâmetro: quem convida (nome e e-mail). Mesmas regras e mensagens das funções do schema api.
export function createMembersStore(inviter: { name: string; email: string }) {
    const state = structuredClone(members)
    const byEmail = (email: string) => state.members.find((m) => m.email === email)

    return {
        list: (): MembersResponse => structuredClone(state),

        invite(req: InviteRequest): InviteResult {
            const result: InviteResult = { invited: [], skipped: [] }
            for (const email of [...new Set(req.emails.map((e) => e.trim().toLowerCase()))]) {
                const member = byEmail(email)
                if (member?.status === 'active') result.skipped.push({ email, reason: 'Já faz parte da organização' })
                else if (member?.status === 'disabled') {
                    result.skipped.push({ email, reason: 'Desativado: reative na lista' })
                } else if (state.invitations.some((i) => i.email === email)) {
                    result.skipped.push({ email, reason: 'Já tem convite pendente' })
                } else {
                    const teamNames = state.teams.filter((t) => req.teams.includes(t.id)).map((t) => t.name)
                    state.invitations.unshift({
                        id: crypto.randomUUID(),
                        email,
                        role: req.role,
                        units: req.role === 'admin' ? [] : req.units,
                        teams: teamNames,
                        invited_by: inviter.name,
                        created_at: daysFromNow(0),
                        expires_at: daysFromNow(7),
                    })
                    result.invited.push(email)
                }
            }
            return result
        },

        setStatus(id: string, status: 'active' | 'disabled', selfEmail: string): Member {
            const member = state.members.find((m) => m.id === id)
            if (!member) throw new DataError(403, 'Você não gere este membro.')
            if (member.email === selfEmail) throw new DataError(409, 'Você não pode desativar a si mesmo.')
            member.status = status
            return structuredClone(member)
        },

        // Acesso (mock/access.ts já conferiu as regras): grava cargos, equipes e o papel na org.
        setAccess(id: string, update: MemberAccessUpdate): Member {
            const member = state.members.find((m) => m.id === id)
            if (!member) throw new DataError(403, 'Você não gere o acesso desta pessoa.')
            member.units = [...update.units].sort((a, b) => a.code.localeCompare(b.code))
            const chosen = state.teams
                .filter((t) => update.teams.includes(t.id))
                .sort((a, b) => a.name.localeCompare(b.name))
            member.teams = chosen.map((t) => t.name)
            member.team_ids = chosen.map((t) => t.id)
            if (update.org_role) member.org_role = update.org_role
            return structuredClone(member)
        },

        revoke(id: string): void {
            const index = state.invitations.findIndex((i) => i.id === id)
            if (index < 0) throw new DataError(409, 'Convite não está mais pendente.')
            state.invitations.splice(index, 1)
        },

        // Como api.accept_my_invitations: o convite do e-mail vira membro ativo.
        accept(email: string): number {
            const normalized = email.trim().toLowerCase()
            const mine = state.invitations.filter((i) => i.email === normalized)
            for (const inv of mine) acceptOne(inv)
            state.invitations = state.invitations.filter((i) => i.email !== normalized)
            return mine.length
        },
    }

    function acceptOne(inv: Invitation) {
        const existing = byEmail(inv.email)
        if (existing?.status === 'disabled') return
        const unitRoles =
            inv.role === 'admin'
                ? []
                : inv.units.map((code) => ({ code, role: inv.role as Exclude<Invitation['role'], 'admin'> }))
        if (existing) {
            existing.status = 'active'
            return
        }
        state.members.push({
            id: crypto.randomUUID(),
            name: inv.email,
            email: inv.email,
            org_role: inv.role === 'admin' ? 'admin' : 'member',
            units: unitRoles,
            teams: inv.teams,
            team_ids: state.teams
                .filter((t) => inv.teams.includes(t.name) && inv.units.includes(t.unit))
                .map((t) => t.id),
            status: 'active',
            last_seen_at: daysFromNow(0),
            security: 'Google',
        })
    }
}
