import { expireSupport } from '../lib/supportSession.ts'
import { DataError } from './errors.ts'

const isExpired = (err: unknown) => err instanceof DataError && err.status === 409 && err.message === 'support_expired'

// Módulo: o fio entre a API e o modo suporte. Toda chamada que rejeita com 409 support_expired encerra o
// modo (expireSupport: limpa a sessão e o provider avisa "A sessão de suporte venceu"). O erro sobe como veio.
// Parâmetro: qualquer cliente (mock ou api). Devolve o mesmo cliente, com os métodos embrulhados.
export function withSupportExpiry<T extends object>(client: T): T {
    const wrapped = { ...client } as Record<string, unknown>
    for (const [name, fn] of Object.entries(client)) {
        if (typeof fn !== 'function') continue
        wrapped[name] = (...args: unknown[]) => {
            const result = (fn as (...a: unknown[]) => unknown).apply(wrapped, args)
            if (!(result instanceof Promise)) return result
            return result.catch((err: unknown) => {
                if (isExpired(err)) expireSupport()
                throw err
            })
        }
    }
    return wrapped as T
}
