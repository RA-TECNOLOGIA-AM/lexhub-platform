import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { SupportSession } from '../types/index.ts'
import { memoryStorage } from './memoryStorage.ts'

const session: SupportSession = {
    sessionId: 's1',
    org: 'lexgroup',
    expiresAt: '2026-11-24T15:00:00Z',
    reason: 'Chamado 42',
    member: {
        membershipId: 'm1',
        name: 'Ana',
        avatarPath: null,
        roleLabel: 'Membro',
        units: [{ code: 'NG', name: 'NG' }],
    },
}

describe('supportSession', () => {
    beforeEach(() => {
        vi.stubGlobal('sessionStorage', memoryStorage()) // o Node 24 (CI) não tem
        vi.resetModules()
    })

    it('set/get sobrevivem a recriar o módulo pelo sessionStorage', async () => {
        const first = await import('./supportSession.ts')
        first.setSupport(session)
        vi.resetModules()
        const second = await import('./supportSession.ts')
        expect(second.getSupport()).toEqual(session)
    })

    it('setSupport(null) limpa a memória e o sessionStorage', async () => {
        const mod = await import('./supportSession.ts')
        mod.setSupport(session)
        mod.setSupport(null)
        expect(mod.getSupport()).toBeNull()
        expect(sessionStorage.getItem('lexhub.support')).toBeNull()
    })

    it('onSupportChange avisa e para de avisar depois de cancelar', async () => {
        const mod = await import('./supportSession.ts')
        const seen: (SupportSession | null)[] = []
        const off = mod.onSupportChange((s) => seen.push(s))
        mod.setSupport(session)
        off()
        mod.setSupport(null)
        expect(seen).toEqual([session])
    })

    it('supportHeaders: vazio sem sessão, com o id durante a sessão', async () => {
        const mod = await import('./supportSession.ts')
        expect(mod.supportHeaders()).toEqual({})
        mod.setSupport(session)
        expect(mod.supportHeaders()).toEqual({ 'X-Support-Session': 's1' })
    })

    it('valor corrompido no sessionStorage vira sem sessão', async () => {
        sessionStorage.setItem('lexhub.support', '{nao-json')
        const mod = await import('./supportSession.ts')
        expect(mod.getSupport()).toBeNull()
    })
})
