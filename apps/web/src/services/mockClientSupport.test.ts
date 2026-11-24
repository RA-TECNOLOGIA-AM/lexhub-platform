import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMockClient } from './mockClient.ts'
import { setSupport } from '../lib/supportSession.ts'
import { DataError } from './errors.ts'
import type { SupportSession } from '../types/index.ts'

const session: SupportSession = {
    sessionId: 's1',
    org: 'lexgroup',
    expiresAt: '2026-11-24T15:00:00Z',
    reason: 'Chamado',
    member: { membershipId: 'm1', name: 'Ana', avatarPath: null, roleLabel: 'Membro', units: [] },
}

describe('mockClient em modo suporte', () => {
    beforeEach(() => {
        sessionStorage.clear()
        // Ambiente node: localStorage falso, em memória.
        const store = new Map<string, string>()
        vi.stubGlobal('localStorage', {
            getItem: (k: string) => store.get(k) ?? null,
            setItem: (k: string, v: string) => void store.set(k, v),
            removeItem: (k: string) => void store.delete(k),
            clear: () => store.clear(),
        })
        sessionStorage.setItem('lexhub.mock.session', 'x')
        setSupport(null)
    })

    it('avatarUrl continua síncrono e não gasta a flag de vencimento', () => {
        setSupport(session)
        localStorage.setItem('lexhub.mock.supportExpired', '1')
        const client = createMockClient()
        expect(client.avatarUrl('a/b.png')).toBe('a/b.png')
        expect(localStorage.getItem('lexhub.mock.supportExpired')).toBe('1')
    })

    it('a flag de vencimento faz a próxima chamada assíncrona dar 409', async () => {
        setSupport(session)
        localStorage.setItem('lexhub.mock.supportExpired', '1')
        await expect(createMockClient().listFavorites('lexgroup')).rejects.toEqual(
            new DataError(409, 'support_expired'),
        )
    })

    it('recriar o cliente com a sessão já guardada mantém o catálogo do membro e as escritas negadas', async () => {
        setSupport(session)
        const client = createMockClient()
        const catalog = await client.listDashboards('lexgroup')
        expect(catalog.available).toHaveLength(2)
        expect(catalog.available.every((d) => !d.can_export && !d.can_toggle)).toBe(true)
        await expect(client.setFavorite('lexgroup', 'x', true)).rejects.toEqual(new DataError(403, 'support_read_only'))
    })
})
