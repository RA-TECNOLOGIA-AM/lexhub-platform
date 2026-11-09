import { DataError } from '../errors.ts'
import type { InviteRequest, MembersResponse } from '../../types/index.ts'

// Os mesmos membros do protótipo.
export const members: MembersResponse = {
    seats: { used: 42, total: 60 },
    teams: [
        { name: 'Protocolo', dashboards: 4 },
        { name: 'Comercial', dashboards: 4 },
        { name: 'Execução', dashboards: 3 },
        { name: 'Diretoria', dashboards: 16 },
    ],
    members: [
        {
            id: 'm1',
            name: 'Ana Ribeiro',
            email: 'ana@lexgroup.com.br',
            role: 'admin',
            units: ['*'],
            team: 'Diretoria',
            status: 'active',
            note: null,
            security: 'MFA ativo',
        },
        {
            id: 'm2',
            name: 'Bruno Melo',
            email: 'bruno@lexgroup.com.br',
            role: 'gestor',
            units: ['NG', 'LA_AM'],
            team: 'Comercial',
            status: 'active',
            note: null,
            security: 'MFA ativo',
        },
        {
            id: 'm3',
            name: 'Carla Souza',
            email: 'carla@lexgroup.com.br',
            role: 'colaborador',
            units: ['LA_RJ'],
            team: 'Protocolo',
            status: 'active',
            note: null,
            security: 'Senha + Google',
        },
        {
            id: 'm4',
            name: 'Fernanda Lopes',
            email: 'fernanda@lexgroup.com.br',
            role: 'leitor',
            units: ['NG'],
            team: 'Diretoria',
            status: 'active',
            note: null,
            security: 'Google',
        },
        {
            id: 'm5',
            name: null,
            email: 'diego@lexgroup.com.br',
            role: 'colaborador',
            units: ['NG'],
            team: 'Pendências',
            status: 'invited',
            note: 'Convidado por Ana Ribeiro há 2 dias',
            security: null,
        },
        {
            id: 'm6',
            name: 'Eduardo Lima',
            email: 'eduardo@lexgroup.com.br',
            role: null,
            units: [],
            team: null,
            status: 'requested',
            note: 'Pediu acesso com Google · domínio verificado',
            security: null,
        },
    ],
}

// Módulo: os membros do mock como um "banco" em memória (volta ao original no F5).
// Parâmetro: o nome de quem convida. Esconde: a lista que muda e a regra de e-mail repetido.
export function createMembersStore(inviterName: string) {
    const state = structuredClone(members)
    return {
        list: (): MembersResponse => structuredClone(state),

        invite(invite: InviteRequest): void {
            const known = new Set(state.members.map((m) => m.email))
            const repeated = invite.emails.filter((e) => known.has(e))
            if (repeated.length) throw new DataError(409, `Já faz parte da organização: ${repeated.join(', ')}`)
            for (const email of invite.emails) {
                state.members.push({
                    id: crypto.randomUUID(),
                    name: null,
                    email,
                    role: invite.role,
                    units: invite.units,
                    team: invite.team,
                    status: 'invited',
                    note: `Convidado por ${inviterName} agora`,
                    security: null,
                })
            }
            state.seats.used += invite.emails.length
        },
    }
}
