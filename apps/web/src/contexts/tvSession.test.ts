import { describe, expect, it, vi } from 'vitest'
import { createTvSession, TV_SESSION_MS, watchTvSession } from './tvSession.ts'

function memoryStorage() {
    const data = new Map<string, string>()
    return {
        getItem: (key: string) => data.get(key) ?? null,
        setItem: (key: string, value: string) => void data.set(key, value),
        removeItem: (key: string) => void data.delete(key),
    }
}

describe('createTvSession', () => {
    it('sem login pela TV não expira nada (login normal não tem prazo)', () => {
        const session = createTvSession(memoryStorage(), () => 0)
        expect(session.expired()).toBe(false)
    })

    it('vale 24 h a partir do login pela TV', () => {
        let now = 1_000
        const session = createTvSession(memoryStorage(), () => now)
        session.start()
        now += TV_SESSION_MS - 1
        expect(session.expired()).toBe(false)
        now += 1
        expect(session.expired()).toBe(true)
    })

    it('clear apaga o prazo (sair, ou login normal no mesmo navegador)', () => {
        let now = 0
        const session = createTvSession(memoryStorage(), () => now)
        session.start()
        session.clear()
        now += TV_SESSION_MS * 2
        expect(session.expired()).toBe(false)
    })

    it('valor estragado no armazenamento conta como vencido (lado seguro)', () => {
        const storage = memoryStorage()
        storage.setItem('lexhub.tv-session-until', 'xyz')
        expect(createTvSession(storage, () => 0).expired()).toBe(true)
    })

    it('sem armazenamento (navegador bloqueou) não quebra', () => {
        const session = createTvSession(null, () => 0)
        session.start()
        expect(session.expired()).toBe(false)
    })
})

describe('watchTvSession com conferência no servidor', () => {
    it('sessão derrubada em outro aparelho: a TV sai no minuto seguinte', async () => {
        vi.useFakeTimers()
        const session = createTvSession(memoryStorage(), () => 0)
        session.start()
        const onExpire = vi.fn()
        const stop = watchTvSession(session, onExpire, { isAlive: async () => false })
        await vi.advanceTimersByTimeAsync(60_000)
        expect(onExpire).toHaveBeenCalledTimes(1)
        stop()
        vi.useRealTimers()
    })

    it('fora de um login pela TV não pergunta nada ao servidor', async () => {
        vi.useFakeTimers()
        const session = createTvSession(memoryStorage(), () => 0)
        const isAlive = vi.fn(async () => false)
        const stop = watchTvSession(session, vi.fn(), { isAlive })
        await vi.advanceTimersByTimeAsync(60_000 * 3)
        expect(isAlive).not.toHaveBeenCalled()
        stop()
        vi.useRealTimers()
    })
})

describe('watchTvSession', () => {
    it('confere de minuto em minuto e chama onExpire uma vez só', () => {
        vi.useFakeTimers()
        let now = 0
        const session = createTvSession(memoryStorage(), () => now)
        session.start()
        const onExpire = vi.fn()
        const stop = watchTvSession(session, onExpire)
        now = TV_SESSION_MS
        vi.advanceTimersByTime(60_000 * 3)
        expect(onExpire).toHaveBeenCalledTimes(1)
        stop()
        vi.useRealTimers()
    })
})
