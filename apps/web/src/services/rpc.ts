import type { SupabaseClient } from '@supabase/supabase-js'
import { toRpcError } from './rpcError.ts'

export type Rpc = <T>(fn: string, args?: Record<string, unknown>) => Promise<T>

// Módulo: chamar uma função do schema api do Supabase e traduzir o erro (rpcError.ts).
// Parâmetro: o cliente do Supabase já logado. Usado pelos clients de Membros, Acesso, Pedidos e Fontes.
export function createRpc(supabase: SupabaseClient): Rpc {
    return async <T>(fn: string, args?: Record<string, unknown>): Promise<T> => {
        const { data, error } = await supabase.schema('api').rpc(fn, args)
        if (error) throw toRpcError(error)
        return data as T
    }
}
