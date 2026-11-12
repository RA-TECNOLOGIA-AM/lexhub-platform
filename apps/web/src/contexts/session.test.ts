import { describe, expect, it } from 'vitest'
import { loadSession } from './session.ts'
import { DataError } from '../services/errors.ts'
import type { Me } from '../types/index.ts'

const me = { org: { slug: 'lexgroup' } } as Me

// Cliente falso: getMe resolve com `me` ou rejeita com o erro dado.
function fakeClient(result: Me | Error, email: string | null = 'pessoa@gmail.com') {
    return {
        getMe: async () => {
            if (result instanceof Error) throw result
            return result
        },
        getSessionEmail: async () => email,
        acceptMyInvitations: async () => 0,
    }
}

describe('loadSession', () => {
    it('com organização: signed-in com o me', async () => {
        expect(await loadSession(fakeClient(me))).toEqual({ status: 'signed-in', me })
    })

    it('403 (logado, sem organização): no-access com o e-mail da sessão', async () => {
        const state = await loadSession(fakeClient(new DataError(403, 'Sem acesso')))
        expect(state).toEqual({ status: 'no-access', email: 'pessoa@gmail.com' })
    })

    it('403 e o e-mail falha: no-access sem e-mail', async () => {
        const client = {
            getMe: async () => {
                throw new DataError(403, 'Sem acesso')
            },
            getSessionEmail: async () => {
                throw new Error('falhou')
            },
            acceptMyInvitations: async () => 0,
        }
        expect(await loadSession(client)).toEqual({ status: 'no-access', email: null })
    })

    it('401 (sem sessão): signed-out', async () => {
        expect(await loadSession(fakeClient(new DataError(401, 'Sessão expirada')))).toEqual({ status: 'signed-out' })
    })

    it('API fora do ar: signed-out', async () => {
        expect(await loadSession(fakeClient(new DataError(0, 'Sem conexão')))).toEqual({ status: 'signed-out' })
    })

    it('aceita os convites pendentes antes de buscar o me (o convidado entra direto)', async () => {
        const order: string[] = []
        const client = {
            getMe: async () => {
                order.push('getMe')
                return me
            },
            getSessionEmail: async () => null,
            acceptMyInvitations: async () => {
                order.push('accept')
                return 1
            },
        }
        await loadSession(client)
        expect(order).toEqual(['accept', 'getMe'])
    })

    it('se aceitar os convites falhar, o login segue', async () => {
        const client = {
            ...fakeClient(me),
            acceptMyInvitations: async () => {
                throw new DataError(500, 'schema api não exposto')
            },
        }
        expect(await loadSession(client)).toEqual({ status: 'signed-in', me })
    })
})
