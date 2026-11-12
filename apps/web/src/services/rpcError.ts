import { DataError } from './errors.ts'

// O que o supabase-js devolve num erro de rpc (só o que usamos).
export type RpcError = { code?: string; message?: string }

// Erro do banco -> DataError com o status que as telas já entendem.
// 42501 = sem permissão (equipe RA ou sem login); P0001 = regra (mensagem já em pt-BR);
// PGRST106 = schema api não exposto no Supabase (configuração).
export function toRpcError(error: RpcError): DataError {
    if (error.code === '42501') return new DataError(403, error.message ?? 'Sem permissão.')
    if (error.code === 'P0001') return new DataError(409, error.message ?? 'Não foi possível concluir.')
    if (error.code === 'PGRST106') {
        return new DataError(500, 'O schema "api" não está exposto no Supabase (Settings > API > Exposed schemas).')
    }
    return new DataError(0, 'Não foi possível falar com o servidor. Tente de novo.')
}
