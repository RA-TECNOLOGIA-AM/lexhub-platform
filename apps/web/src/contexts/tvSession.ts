// Módulo: o prazo da sessão aberta pelo login da TV (QR Code).
// Parâmetros: onde guardar (localStorage), o relógio e a duração.
// Esconde: a chave, o formato e o que fazer com valor estragado.
// Só o login pela TV tem prazo; login normal (Google/senha) continua como sempre.

export const TV_SESSION_MS = 24 * 60 * 60 * 1_000

const KEY = 'lexhub.tv-session-until'

type KeyValue = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>

export type TvSession = {
    start(): void // login pela TV: a sessão vale TV_SESSION_MS a partir de agora
    clear(): void // sair, ou login normal no mesmo navegador
    active(): boolean // este navegador entrou pelo QR (com prazo, vencido ou não)
    expired(): boolean
}

export function createTvSession(
    storage: KeyValue | null,
    now: () => number = () => Date.now(),
    ttlMs: number = TV_SESSION_MS,
): TvSession {
    const read = (): string | null => {
        try {
            return storage?.getItem(KEY) ?? null
        } catch {
            return null
        }
    }
    return {
        start() {
            try {
                storage?.setItem(KEY, String(now() + ttlMs))
            } catch {
                // armazenamento bloqueado: a TV fica sem prazo, como um login normal
            }
        },
        clear() {
            try {
                storage?.removeItem(KEY)
            } catch {
                // nada a apagar
            }
        },
        active() {
            return read() !== null
        },
        expired() {
            const value = read()
            if (value === null) return false
            const until = Number(value)
            // Valor estragado: trata como vencido (pede o QR de novo em vez de ficar logado para sempre).
            return !Number.isFinite(until) || now() >= until
        },
    }
}

type WatchOptions = {
    everyMs?: number
    // Pergunta ao servidor se a sessão ainda existe (ex.: "Desconectar outros aparelhos" no celular).
    // false = derrubada; erro de rede deve responder true (TV não sai por Wi-Fi instável).
    isAlive?: () => Promise<boolean>
}

// Confere de minuto em minuto, e quando a aba volta a aparecer (TV que dormiu atrasa timers):
// o prazo de 24 h e, se houver isAlive, se a sessão não foi derrubada em outro aparelho.
// Sem login pela TV neste navegador, não faz nada. Devolve stop().
export function watchTvSession(
    session: TvSession,
    onExpire: () => void,
    { everyMs = 60_000, isAlive }: WatchOptions = {},
): () => void {
    let fired = false
    let asking = false
    const fire = () => {
        if (fired) return
        fired = true
        onExpire()
    }
    const check = () => {
        if (fired || !session.active()) return
        if (session.expired()) return fire()
        if (!isAlive || asking) return
        asking = true
        isAlive()
            .then((alive) => {
                if (!alive) fire()
            })
            .catch(() => {})
            .finally(() => {
                asking = false
            })
    }
    const timer = setInterval(check, everyMs)
    const onVisible = () => {
        if (typeof document !== 'undefined' && document.visibilityState === 'visible') check()
    }
    if (typeof document !== 'undefined') document.addEventListener('visibilitychange', onVisible)
    return () => {
        clearInterval(timer)
        if (typeof document !== 'undefined') document.removeEventListener('visibilitychange', onVisible)
    }
}

function browserStorage(): KeyValue | null {
    try {
        return typeof window === 'undefined' ? null : window.localStorage
    } catch {
        return null
    }
}

export const tvSession = createTvSession(browserStorage())
