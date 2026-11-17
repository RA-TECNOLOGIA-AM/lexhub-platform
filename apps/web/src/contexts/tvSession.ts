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
        expired() {
            const value = read()
            if (value === null) return false
            const until = Number(value)
            // Valor estragado: trata como vencido (pede o QR de novo em vez de ficar logado para sempre).
            return !Number.isFinite(until) || now() >= until
        },
    }
}

// Confere o prazo de minuto em minuto e quando a aba volta a aparecer
// (TV que dormiu ou aba em segundo plano atrasa timers longos). Devolve stop().
export function watchTvSession(session: TvSession, onExpire: () => void, everyMs = 60_000): () => void {
    let fired = false
    const check = () => {
        if (!fired && session.expired()) {
            fired = true
            onExpire()
        }
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
