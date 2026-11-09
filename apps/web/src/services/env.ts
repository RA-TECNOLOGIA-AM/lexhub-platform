// Variáveis do .env.local (mesmos nomes do front da v1). Todas VITE_*: públicas, nunca segredo.
// Módulo: o único lugar que lê import.meta.env; o resto do app recebe os valores prontos.

export type DataSource = 'mock' | 'api'

export const env = {
    dataSource: (import.meta.env.VITE_DATA_SOURCE ?? 'mock') as string,
    apiUrl: (import.meta.env.VITE_BASE_API_URL ?? '') as string,
    supabaseUrl: (import.meta.env.VITE_SUPABASE_URL ?? '') as string,
    supabaseAnonKey: (import.meta.env.VITE_SUPABASE_ANON_KEY ?? '') as string,
    siteUrl: (import.meta.env.VITE_SITE_URL ?? window.location.origin) as string,
}

// Falha cedo e com mensagem clara quando falta uma variável obrigatória do modo escolhido.
export function required(name: string, value: string): string {
    if (!value) throw new Error(`Falta ${name} no apps/web/.env.local (veja o .env.example)`)
    return value
}
