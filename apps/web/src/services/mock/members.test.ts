import { describe, expect, it } from 'vitest'
import { createMembersStore } from './members.ts'
import { DataError } from '../errors.ts'

const inviter = { name: 'Ana Ribeiro', email: 'ana@lexgroup.com.br' }

describe('createMembersStore', () => {
    it('convite repetido volta em skipped, sem erro', () => {
        const store = createMembersStore(inviter)
        const req = { emails: ['nova@exemplo.com'], role: 'leitor' as const, units: ['NG'], teams: [] }
        expect(store.invite(req)).toEqual({ invited: ['nova@exemplo.com'], skipped: [] })
        expect(store.invite(req)).toEqual({
            invited: [],
            skipped: [{ email: 'nova@exemplo.com', reason: 'Já tem convite pendente' }],
        })
        const invitation = store.list().invitations.find((i) => i.email === 'nova@exemplo.com')
        expect(invitation).toMatchObject({ role: 'leitor', units: ['NG'], invited_by: 'Ana Ribeiro' })
    })

    it('quem já é membro ativo é pulado com o motivo', () => {
        const result = createMembersStore(inviter).invite({
            emails: ['carla@lexgroup.com.br'],
            role: 'leitor',
            units: ['NG'],
            teams: [],
        })
        expect(result.skipped).toEqual([{ email: 'carla@lexgroup.com.br', reason: 'Já faz parte da organização' }])
    })

    it('ninguém desativa a si mesmo', () => {
        const store = createMembersStore(inviter)
        const ana = store.list().members.find((m) => m.email === inviter.email)!
        expect(() => store.setStatus(ana.id, 'disabled', inviter.email)).toThrow(
            new DataError(409, 'Você não pode desativar a si mesmo.'),
        )
    })

    it('desativa e reativa outra pessoa', () => {
        const store = createMembersStore(inviter)
        const carla = store.list().members.find((m) => m.email === 'carla@lexgroup.com.br')!
        expect(store.setStatus(carla.id, 'disabled', inviter.email).status).toBe('disabled')
        expect(store.setStatus(carla.id, 'active', inviter.email).status).toBe('active')
    })

    it('aceitar o convite cria o membro ativo com o cargo nas unidades do convite', () => {
        const store = createMembersStore(inviter)
        store.invite({ emails: ['nova@exemplo.com'], role: 'controller', units: ['LA_AM'], teams: [] })
        expect(store.accept('NOVA@exemplo.com')).toBe(1)
        const nova = store.list().members.find((m) => m.email === 'nova@exemplo.com')
        expect(nova).toMatchObject({
            status: 'active',
            org_role: 'member',
            units: [{ code: 'LA_AM', role: 'controller' }],
        })
        expect(store.list().invitations.some((i) => i.email === 'nova@exemplo.com')).toBe(false)
    })

    it('cancelar o convite tira da lista', () => {
        const store = createMembersStore(inviter)
        const pending = store.list().invitations[0]
        store.revoke(pending.id)
        expect(store.list().invitations.some((i) => i.id === pending.id)).toBe(false)
    })
})
