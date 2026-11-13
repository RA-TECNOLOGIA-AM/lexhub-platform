import type { SupabaseClient } from '@supabase/supabase-js'

// Só para testes: Supabase falso que guarda o schema, a função e os parâmetros de cada rpc e devolve `result`.
export function fakeSupabase(result: { data?: unknown; error?: { code?: string; message?: string } }) {
    const calls: { schema: string; fn: string; args: unknown }[] = []
    const supabase = {
        schema: (schema: string) => ({
            rpc: async (fn: string, args?: unknown) => {
                calls.push({ schema, fn, args })
                return { data: result.data ?? null, error: result.error ?? null }
            },
        }),
    } as unknown as SupabaseClient
    return { supabase, calls }
}
