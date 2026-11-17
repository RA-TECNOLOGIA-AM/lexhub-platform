import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { DataError } from '../../services/errors.ts'
import type { DeviceCodeResponse, DeviceTokenResult } from '../../services/client.ts'
import { DEVICE_LOGIN, startDeviceLogin, type DeviceLoginClient } from './deviceLogin.ts'

function code(n: number): DeviceCodeResponse {
    return {
        device_code: `device-${n}`,
        user_code: `AAAA-000${n}`,
        verification_uri: `https://hub/ativar?code=AAAA-000${n}`,
        interval: 5,
        expires_in: 600,
    }
}

const timers = {
    set: (fn: () => void, ms: number) => setTimeout(fn, ms),
    clear: (handle: unknown) => clearTimeout(handle as ReturnType<typeof setTimeout>),
    now: () => Date.now(),
}

function setup(polls: Array<DeviceTokenResult | Error | 'hang'>) {
    let created = 0
    const pollTimes: number[] = []
    const client: DeviceLoginClient = {
        createDeviceCode: vi.fn(async () => code(++created)),
        pollDeviceToken: vi.fn(async () => {
            pollTimes.push(Date.now())
            const next = polls.shift() ?? { status: 'authorization_pending' }
            if (next === 'hang') return new Promise<DeviceTokenResult>(() => {})
            if (next instanceof Error) throw next
            return next
        }),
    }
    const events = {
        onCode: vi.fn(),
        onProblem: vi.fn(),
        onApproved: vi.fn(async () => {}),
    }
    const stop = startDeviceLogin(client, events, timers)
    return { client, events, stop, pollTimes }
}

const approved: DeviceTokenResult = { status: 'approved', access_token: 'a', refresh_token: 'r', expires_in: 3600 }
const step = DEVICE_LOGIN.pollMarginMs + 5_000

describe('startDeviceLogin', () => {
    beforeEach(() => {
        vi.useFakeTimers()
    })
    afterEach(() => {
        vi.useRealTimers()
    })

    it('consulta só depois da resposta anterior, com folga sobre o intervalo do servidor', async () => {
        const { pollTimes, stop } = setup([])
        await vi.advanceTimersByTimeAsync(step * 3)
        expect(pollTimes).toHaveLength(3)
        for (let i = 1; i < pollTimes.length; i++) {
            expect(pollTimes[i] - pollTimes[i - 1]).toBeGreaterThan(5_000)
        }
        stop()
    })

    it('slow_down espera mais só uma vez e volta ao ritmo normal', async () => {
        const { pollTimes, stop } = setup([{ status: 'slow_down' }])
        await vi.advanceTimersByTimeAsync(step + (step + 5_000) + step)
        expect(pollTimes).toHaveLength(3)
        expect(pollTimes[1] - pollTimes[0]).toBe(step + 5_000)
        expect(pollTimes[2] - pollTimes[1]).toBe(step)
        stop()
    })

    it('aprovado entrega a sessão e para de consultar', async () => {
        const { events, pollTimes, stop } = setup([approved])
        await vi.advanceTimersByTimeAsync(step * 4)
        expect(events.onApproved).toHaveBeenCalledWith({ access_token: 'a', refresh_token: 'r', expires_in: 3600 })
        expect(pollTimes).toHaveLength(1)
        stop()
    })

    it('código expirado vira QR novo sozinho (TV não tem quem clique)', async () => {
        const { events, client, stop } = setup([{ status: 'expired_token' }])
        await vi.advanceTimersByTimeAsync(step)
        expect(client.createDeviceCode).toHaveBeenCalledTimes(2)
        expect(events.onCode).toHaveBeenLastCalledWith(code(2))
        stop()
    })

    it('prazo local vencido gera QR novo sem consultar o código velho', async () => {
        const { client, stop } = setup([])
        await vi.advanceTimersByTimeAsync(600_000 + step)
        expect(client.createDeviceCode).toHaveBeenCalledTimes(2)
        stop()
    })

    it('falha de rede avisa e continua tentando; a próxima resposta limpa o aviso', async () => {
        const { events, pollTimes, stop } = setup([new DataError(0, 'sem rede')])
        await vi.advanceTimersByTimeAsync(step)
        expect(events.onProblem).toHaveBeenLastCalledWith(expect.stringContaining('Tentando de novo'))
        await vi.advanceTimersByTimeAsync(DEVICE_LOGIN.retryMs)
        expect(pollTimes).toHaveLength(2)
        expect(events.onProblem).toHaveBeenLastCalledWith(null)
        stop()
    })

    it('consulta travada estoura o tempo e a TV segue consultando', async () => {
        const { pollTimes, events, stop } = setup(['hang'])
        await vi.advanceTimersByTimeAsync(step + DEVICE_LOGIN.requestTimeoutMs + DEVICE_LOGIN.retryMs)
        expect(events.onProblem).toHaveBeenCalledWith(expect.stringContaining('Tentando de novo'))
        expect(pollTimes).toHaveLength(2)
        stop()
    })

    it('falha ao gerar o código tenta de novo sozinha', async () => {
        let calls = 0
        const client: DeviceLoginClient = {
            createDeviceCode: vi.fn(async () => {
                if (++calls === 1) throw new DataError(503, 'fora do ar')
                return code(calls)
            }),
            pollDeviceToken: vi.fn(async () => ({ status: 'authorization_pending' }) as DeviceTokenResult),
        }
        const events = { onCode: vi.fn(), onProblem: vi.fn(), onApproved: vi.fn(async () => {}) }
        const stop = startDeviceLogin(client, events, timers)
        await vi.advanceTimersByTimeAsync(0)
        expect(events.onProblem).toHaveBeenCalledWith(expect.stringContaining('fora do ar'))
        await vi.advanceTimersByTimeAsync(DEVICE_LOGIN.retryMs)
        expect(events.onCode).toHaveBeenCalledWith(code(2))
        stop()
    })

    it('erro ao abrir a sessão aprovada gera um QR novo', async () => {
        const { events, client, stop } = setup([approved])
        events.onApproved.mockRejectedValueOnce(new DataError(409, 'já consumido'))
        await vi.advanceTimersByTimeAsync(step + DEVICE_LOGIN.retryMs)
        expect(client.createDeviceCode).toHaveBeenCalledTimes(2)
        stop()
    })

    it('stop cancela tudo', async () => {
        const { pollTimes, stop } = setup([])
        await vi.advanceTimersByTimeAsync(0)
        stop()
        await vi.advanceTimersByTimeAsync(step * 5)
        expect(pollTimes).toHaveLength(0)
    })
})
