import { DataError } from '../../services/errors.ts'
import type { DeviceCodeResponse, DeviceSession, DeviceTokenResult } from '../../services/client.ts'

// Módulo: o laço de login da TV (gera o QR, consulta até aprovarem, refaz o QR quando vence).
// Parâmetros: o cliente (de onde vêm código e consulta), os avisos para a tela e o relógio.
// Esconde: ritmo das consultas, timeout, novas tentativas e troca automática do código.
// A TV fica sozinha na parede: nada aqui espera alguém clicar.

export type DeviceLoginClient = {
    createDeviceCode(): Promise<DeviceCodeResponse>
    pollDeviceToken(deviceCode: string): Promise<DeviceTokenResult>
}

export type DeviceLoginEvents = {
    onCode(code: DeviceCodeResponse): void // QR novo para mostrar
    onProblem(message: string | null): void // aviso passageiro (o laço continua sozinho); null = some o aviso
    onApproved(session: DeviceSession): Promise<void> // abrir a sessão; se rejeitar, o laço gera um QR novo
}

export type DeviceLoginTimers = {
    set(fn: () => void, ms: number): unknown
    clear(handle: unknown): void
    now(): number
}

export const DEVICE_LOGIN = {
    // Folga sobre o intervalo do servidor: ele recusa (slow_down) consulta que chega antes de 5 s.
    pollMarginMs: 500,
    // Consulta pendurada (Wi-Fi da TV caiu no meio) não pode parar o laço.
    requestTimeoutMs: 15_000,
    // Falha: tenta de novo em 10 s, 20 s, 30 s (teto).
    retryMs: 10_000,
    maxRetryMs: 30_000,
    // slow_down: espera estes segundos a mais na próxima consulta (RFC 8628).
    slowDownMs: 5_000,
}

const browserTimers: DeviceLoginTimers = {
    set: (fn, ms) => window.setTimeout(fn, ms),
    clear: (handle) => window.clearTimeout(handle as number),
    now: () => Date.now(),
}

function messageOf(reason: unknown, fallback: string): string {
    return reason instanceof DataError && reason.message ? `${reason.message} Tentando de novo…` : fallback
}

// Devolve stop(): para tudo (sair da tela, desmontar o componente).
export function startDeviceLogin(
    client: DeviceLoginClient,
    events: DeviceLoginEvents,
    timers: DeviceLoginTimers = browserTimers,
): () => void {
    let stopped = false
    let handle: unknown
    let failures = 0
    let current: DeviceCodeResponse | null = null
    let deadline = 0

    const schedule = (fn: () => void, ms: number) => {
        if (!stopped) handle = timers.set(fn, ms)
    }
    const retryDelay = () => Math.min(DEVICE_LOGIN.retryMs * 2 ** Math.max(failures - 1, 0), DEVICE_LOGIN.maxRetryMs)
    const pollDelay = (extra = 0) => (current ? current.interval * 1_000 : 5_000) + DEVICE_LOGIN.pollMarginMs + extra

    function withTimeout<T>(promise: Promise<T>): Promise<T> {
        return new Promise<T>((resolve, reject) => {
            const timer = timers.set(
                () => reject(new DataError(0, 'A conexão está lenta.')),
                DEVICE_LOGIN.requestTimeoutMs,
            )
            promise.then(
                (value) => {
                    timers.clear(timer)
                    resolve(value)
                },
                (reason: unknown) => {
                    timers.clear(timer)
                    reject(reason)
                },
            )
        })
    }

    function recovered() {
        if (failures > 0) {
            failures = 0
            events.onProblem(null)
        }
    }

    async function newCode() {
        try {
            const code = await withTimeout(client.createDeviceCode())
            if (stopped) return
            current = code
            deadline = timers.now() + code.expires_in * 1_000
            recovered()
            events.onCode(code)
            schedule(() => void poll(), pollDelay())
        } catch (reason) {
            if (stopped) return
            failures++
            events.onProblem(messageOf(reason, 'Não foi possível gerar o QR Code. Tentando de novo…'))
            schedule(() => void newCode(), retryDelay())
        }
    }

    async function poll() {
        if (!current || timers.now() >= deadline) return newCode()

        let result: DeviceTokenResult
        try {
            result = await withTimeout(client.pollDeviceToken(current.device_code))
        } catch (reason) {
            if (stopped) return
            // Código que o servidor não conhece mais (consumido, apagado): começa de novo.
            if (reason instanceof DataError && reason.code === 'invalid_grant') return newCode()
            failures++
            events.onProblem('Conexão instável com o LexHub. Tentando de novo…')
            schedule(() => void poll(), Math.max(pollDelay(), retryDelay()))
            return
        }
        if (stopped) return
        recovered()

        if (result.status === 'authorization_pending') return schedule(() => void poll(), pollDelay())
        // Só a próxima consulta espera mais: depois volta ao ritmo normal (a folga evita repetir).
        if (result.status === 'slow_down') return schedule(() => void poll(), pollDelay(DEVICE_LOGIN.slowDownMs))
        if (result.status !== 'approved') return newCode() // expired_token

        try {
            await events.onApproved({
                access_token: result.access_token,
                refresh_token: result.refresh_token,
                expires_in: result.expires_in,
            })
        } catch (reason) {
            if (stopped) return
            failures++
            events.onProblem(messageOf(reason, 'Não foi possível entrar na TV. Gerando um novo QR Code…'))
            schedule(() => void newCode(), retryDelay())
        }
    }

    void newCode()
    return () => {
        stopped = true
        timers.clear(handle)
    }
}
