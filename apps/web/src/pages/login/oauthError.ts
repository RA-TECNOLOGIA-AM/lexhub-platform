// Módulo: traduz o erro com que o Supabase devolve o login do Google para o /login
// (?error=...&error_description=..., ou no #hash) numa mensagem FIXA do app.
// O texto da URL nunca vai para a tela: qualquer um monta um link /login?error_description=<mentira>.
// Ele só serve para escolher qual das mensagens fixas mostrar.
// Parâmetros: search e hash da URL (window.location). Devolve null quando não há erro.

export const NO_INVITE_MESSAGE =
    'Este e-mail não tem convite para o LexHub. Peça um convite ao administrador e entre com a conta Google convidada.'
export const GENERIC_OAUTH_MESSAGE = 'Não foi possível entrar com o Google. Tente de novo.'

// Pedaço da mensagem do hook app_private.hook_before_user_created ("Sem convite para o LexHub.").
const HOOK_MARKER = 'sem convite'

export function oauthErrorMessage(search: string, hash: string): string | null {
    const query = new URLSearchParams(search)
    const fragment = new URLSearchParams(hash.startsWith('#') ? hash.slice(1) : hash)
    const error = query.get('error') ?? fragment.get('error')
    if (!error) return null
    // URLSearchParams já decodifica (%C3%A3 e +).
    const description = (query.get('error_description') ?? fragment.get('error_description') ?? '').toLowerCase()
    return description.includes(HOOK_MARKER) ? NO_INVITE_MESSAGE : GENERIC_OAUTH_MESSAGE
}
