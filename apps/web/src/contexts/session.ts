import type { DataClient } from '../services/client.ts'
import { DataError } from '../services/errors.ts'
import type { Me } from '../types/index.ts'

// Os três jeitos de abrir o app:
// - signed-in: tem sessão e faz parte de ao menos uma organização;
// - no-access: tem sessão (ex.: entrou com o Google), mas não está em nenhuma organização (403 no /me);
// - signed-out: sem sessão (401) ou a API não respondeu.
export type SessionState =
    { status: 'signed-in'; me: Me } | { status: 'no-access'; email: string | null } | { status: 'signed-out' }

// Módulo: descobre em que estado está a sessão, sem React (testado em session.test.ts).
// Parâmetros: o cliente de dados (só getMe e getSessionEmail). Usa a organização padrão:
// aqui, um 403 só pode querer dizer "nenhuma organização".
export async function loadSession(client: Pick<DataClient, 'getMe' | 'getSessionEmail'>): Promise<SessionState> {
    try {
        return { status: 'signed-in', me: await client.getMe() }
    } catch (err) {
        if (err instanceof DataError && err.status === 403) {
            const email = await client.getSessionEmail().catch(() => null)
            return { status: 'no-access', email }
        }
        return { status: 'signed-out' }
    }
}
