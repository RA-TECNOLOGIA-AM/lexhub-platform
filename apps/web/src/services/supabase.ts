import { createClient, type SupabaseClient } from '@supabase/supabase-js'

// Módulo: o cliente do Supabase, usado SÓ para o login (Supabase Auth).
// Os dados nunca vêm daqui: passam pela API, que decide o acesso.
// Parâmetros: URL do projeto e a anon key (pública por natureza).
// pkce: o Google devolve um código (?code=) que o próprio cliente troca pela sessão ao abrir a página
// (detectSessionInUrl); o token nunca aparece na URL.
export function createSupabaseAuth(url: string, anonKey: string): SupabaseClient {
    return createClient(url, anonKey, {
        auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, flowType: 'pkce' },
    })
}
