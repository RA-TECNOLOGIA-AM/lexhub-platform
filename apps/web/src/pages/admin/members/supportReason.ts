// Módulo: a regra do motivo do modo suporte (igual à do servidor: 5 a 500 caracteres, sem as pontas).
export const REASON_MIN = 5
export const REASON_MAX = 500

// O motivo como o servidor vai gravar (sem os espaços das pontas) e se já pode começar.
export function reasonState(text: string): { reason: string; length: number; ok: boolean } {
    const reason = text.trim()
    return { reason, length: reason.length, ok: reason.length >= REASON_MIN && reason.length <= REASON_MAX }
}
