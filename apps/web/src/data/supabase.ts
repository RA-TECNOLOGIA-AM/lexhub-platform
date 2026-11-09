import { createClient, type SupabaseClient } from '@supabase/supabase-js'

// Módulo: o cliente do Supabase, usado SÓ para o login (Supabase Auth).
// Os dados nunca vêm daqui: passam pela API, que decide o acesso.
// Parâmetros: URL do projeto e a anon key (pública por natureza).
export function createSupabaseAuth(url: string, anonKey: string): SupabaseClient {
    return createClient(url, anonKey, {
        auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
    })
}
