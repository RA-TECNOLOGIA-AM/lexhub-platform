import type { SupportSession } from '../types/index.ts'

const KEY = 'lexhub.support'

// O texto no lugar das ações de escrita (exportar...) durante o modo suporte.
export const SUPPORT_READ_ONLY = 'Somente leitura no modo suporte'

// Módulo: a sessão de suporte (Owner/Dev vendo como um membro) desta aba.
// Esconde: onde ela mora (memória + sessionStorage, que some ao fechar a aba) e o cabeçalho que a API espera.
// Devolve: ler, gravar (null = sair), assinar mudanças e o cabeçalho de toda chamada à API.
function load(): SupportSession | null {
    try {
        const raw = sessionStorage.getItem(KEY)
        return raw ? (JSON.parse(raw) as SupportSession) : null
    } catch {
        return null // sessionStorage indisponível ou valor corrompido: sem sessão
    }
}

let current: SupportSession | null = load()
const listeners = new Set<(s: SupportSession | null) => void>()

export function getSupport(): SupportSession | null {
    return current
}

export function setSupport(s: SupportSession | null): void {
    current = s
    try {
        if (s) sessionStorage.setItem(KEY, JSON.stringify(s))
        else sessionStorage.removeItem(KEY)
    } catch {
        // sem sessionStorage: vale só na memória
    }
    listeners.forEach((fn) => fn(s))
}

// Devolve a função que cancela a assinatura.
export function onSupportChange(fn: (s: SupportSession | null) => void): () => void {
    listeners.add(fn)
    return () => {
        listeners.delete(fn)
    }
}

// Durante o suporte, toda chamada à API leva o id da sessão; fora dele, nada.
export function supportHeaders(): Record<string, string> {
    return current ? { 'X-Support-Session': current.sessionId } : {}
}

// A sessão venceu (409 support_expired da API ou o relógio local no expiresAt): sai do modo e avisa quem
// assina com a sessão que acabou (o provider mostra "A sessão de suporte venceu"). Sem sessão, não faz nada
// (ex.: resposta atrasada depois de Sair).
const expiredListeners = new Set<(ended: SupportSession) => void>()

export function expireSupport(): void {
    const ended = current
    if (!ended) return
    setSupport(null)
    expiredListeners.forEach((fn) => fn(ended))
}

// Devolve a função que cancela a assinatura.
export function onSupportExpired(fn: (ended: SupportSession) => void): () => void {
    expiredListeners.add(fn)
    return () => {
        expiredListeners.delete(fn)
    }
}

// Primeiro trecho da URL que não é organização (rotas fora de /:org).
const NOT_ORG = new Set(['plataforma', 'login', 'ativar', 'tv-login'])

// A sessão guardada ainda vale nesta tela? Não vale se venceu ou se a URL é de outra organização:
// o cabeçalho de suporte nunca vai para outra org. Rotas fora de organização não decidem (redirecionam ao hub).
export function supportValidFor(s: SupportSession, pathname: string, now: number = Date.now()): boolean {
    if (Date.parse(s.expiresAt) <= now) return false
    const first = pathname.split('/')[1] ?? ''
    return !first || NOT_ORG.has(first) || first === s.org
}
