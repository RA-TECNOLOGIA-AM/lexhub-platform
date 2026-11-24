import { describe, expect, it, vi } from 'vitest'
import { createBeat } from './usePresenceHeartbeat.ts'

describe('createBeat', () => {
    it('sessão viva: só avisa presença', async () => {
        const onSessionGone = vi.fn()
        const touch = vi.fn(async () => {})
        await createBeat({ touch, isAlive: async () => true, onSessionGone })()
        expect(touch).toHaveBeenCalledOnce()
        expect(onSessionGone).not.toHaveBeenCalled()
    })

    it('sessão derrubada: chama onSessionGone uma vez só', async () => {
        const onSessionGone = vi.fn()
        const beat = createBeat({ touch: async () => {}, isAlive: async () => false, onSessionGone })
        await beat()
        await beat()
        expect(onSessionGone).toHaveBeenCalledOnce()
    })

    it('falha ao conferir ou ao avisar presença: não tira a pessoa', async () => {
        const onSessionGone = vi.fn()
        await createBeat({
            touch: async () => Promise.reject(new Error('rede')),
            isAlive: async () => Promise.reject(new Error('rede')),
            onSessionGone,
        })()
        expect(onSessionGone).not.toHaveBeenCalled()
    })
})
