import { describe, expect, it } from 'vitest'
import type { Member } from '../../../types/index.ts'
import { DataError } from '../../../services/errors.ts'
import { accessMemberOf, loadAccessMembers } from './accessMember.ts'

const base: Member = {
    id: 'm1',
    name: 'Pessoa',
    email: 'pessoa@exemplo.com',
    org_role: 'member',
    units: [],
    teams: [],
    status: 'active',
    last_seen_at: null,
    security: null,
}

describe('accessMemberOf', () => {
    it('cargo de maior nível entre as unidades; Controller vira Gestor (a matriz ainda não tem Controller)', () => {
        const m = {
            ...base,
            units: [
                { code: 'NG', role: 'leitor' as const },
                { code: 'LA_AM', role: 'controller' as const },
            ],
            teams: ['Comercial'],
        }
        expect(accessMemberOf(m)).toMatchObject({ role: 'gestor', units: ['NG', 'LA_AM'], team: 'Comercial' })
    })

    it('Desenvolvedor vale em todas as unidades', () => {
        expect(accessMemberOf({ ...base, org_role: 'admin' })).toMatchObject({
            role: 'admin',
            units: ['*'],
            team: null,
        })
    })
})

describe('loadAccessMembers', () => {
    it('quem não gere membros (403) abre o Acesso com o simulador vazio, sem quebrar a página', async () => {
        const client = {
            listMembers: async () => {
                throw new DataError(403, 'Você não gere membros nesta organização.')
            },
        }
        expect(await loadAccessMembers(client, 'lexgroup')).toEqual([])
    })
    it('outros erros continuam subindo', async () => {
        const client = {
            listMembers: async () => {
                throw new DataError(0, 'Sem conexão')
            },
        }
        await expect(loadAccessMembers(client, 'lexgroup')).rejects.toThrow('Sem conexão')
    })
})
