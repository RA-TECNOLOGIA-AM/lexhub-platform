import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useSearchParams } from 'react-router'
import { useAuth } from '../contexts/auth-context.ts'
import { GoogleMark } from '../components/ui/GoogleMark.tsx'
import { Icon } from '../components/ui/Icon.tsx'
import { PasswordInput } from '../components/ui/PasswordInput.tsx'
import { DataError } from '../services/errors.ts'
import { NoAccessCard } from './login/NoAccessCard.tsx'
import { oauthErrorMessage } from './login/oauthError.ts'
import { usePageTransition } from '../components/page_transition/usePageTransition.ts'
import { LoadingState } from '../components/states/LoadingState.tsx'

function internalPath(value: string | null | undefined): string | null {
    if (!value || !value.startsWith('/') || value.startsWith('//') || value.includes('\\')) return null
    try {
        const url = new URL(value, window.location.origin)
        return url.origin === window.location.origin ? `${url.pathname}${url.search}${url.hash}` : null
    } catch {
        return null
    }
}

// Entrada: Google (principal) ou e-mail + senha, e entrada por convite (?convite=<token>).
// ?estado=sessao-expirada = veio de um 401 da API.
// Logado sem organização (403 no /me): o card vira "sem acesso" (NoAccessCard).
export function LoginPage() {
    const { me, noAccess, loading, signIn, signInWithGoogle, signOut } = useAuth()
    const location = useLocation()
    const [params] = useSearchParams()
    const { transitionTo } = usePageTransition()
    const invite = params.get('convite')

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [submitting, setSubmitting] = useState(false)
    const [googleSignInStarted, setGoogleSignInStarted] = useState(false)
    const transitionStarted = useRef(false)
    // Volta do Google com erro (ex.: e-mail sem convite, barrado pelo hook do Supabase): mensagem fixa.
    const [error, setError] = useState(
        () =>
            oauthErrorMessage(location.search, location.hash) ??
            (params.get('estado') === 'sessao-expirada' ? 'Sua sessão expirou. Entre de novo para continuar.' : ''),
    )

    const from =
        internalPath((location.state as { from?: string } | null)?.from) ?? internalPath(params.get('returnTo'))
    const destination = me ? (from ?? `/${me.org.slug}/dashboards`) : null
    const isGoogleSignIn = params.has('code') || googleSignInStarted

    useEffect(() => {
        if (!destination || !isGoogleSignIn || transitionStarted.current) return
        transitionStarted.current = true
        transitionTo(destination)
    }, [destination, isGoogleSignIn, transitionTo])

    // Ainda conferindo a sessão (volta do Google, F5 no /login): a logo da abertura do app continua na tela.
    // Sem isso o formulário aparecia nesse meio-tempo, a logo saía e voltava depois para levar ao hub.
    if (loading) return <LoadingState />

    // Logado (já estava, ou acabou de entrar): volta para onde queria ir, ou para o hub.
    if (me) {
        // Volta do Google: a logo segue na tela até o transitionTo acima levar ao destino.
        if (isGoogleSignIn) return <LoadingState />
        return <Navigate to={from ?? `/${me.org.slug}/dashboards`} replace />
    }

    async function handleSubmit(e: FormEvent<HTMLFormElement>) {
        e.preventDefault() // impede o navegador de recarregar a página
        if (!email || !password) {
            setError('Preencha e-mail e senha.')
            return
        }
        // Só formato (tem algo@algo.algo). Não é segurança: é para pegar erro de digitação cedo.
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
            setError('Digite um e-mail válido.')
            return
        }
        setError('')
        setSubmitting(true)
        try {
            await signIn(email, password) // deu certo: o "if (me)" acima faz o redirecionamento
        } catch (err) {
            setError(err instanceof DataError ? err.message : 'Não foi possível entrar. Tente de novo.')
        }
        setSubmitting(false)
    }

    // Na API, a página sai para o Google; o botão fica em "Abrindo o Google…" até lá.
    async function handleGoogle() {
        setError('')
        setGoogleSignInStarted(true)
        setSubmitting(true)
        try {
            await signInWithGoogle(from ?? undefined)
        } catch (err) {
            setError(err instanceof DataError ? err.message : 'Não foi possível abrir o login do Google.')
            setGoogleSignInStarted(false)
            setSubmitting(false)
        }
    }

    return (
        <main className="auth">
            <div className="card auth-card">
                <div className="brand">
                    <span className="brand-mark">
                        <img src="/logo-justica.svg" alt="" width={24} height={24} />
                    </span>
                    <span>LexHub</span>
                </div>

                {noAccess ? (
                    <NoAccessCard email={noAccess.email} onSignOut={() => void signOut()} />
                ) : (
                    <>
                        <div className="stack" style={{ gap: 6 }}>
                            <h1 className="h1" style={{ fontSize: 24 }}>
                                {invite ? 'Aceitar convite' : 'Bem-vindo de volta'}
                            </h1>
                            <p className="muted small">Entre com a sua conta para acessar o LexHub.</p>
                        </div>

                        {invite && (
                            <div className="notice info">
                                <Icon name="info" />
                                <div className="small">
                                    Você foi convidado para <strong>LexGroup · NG</strong>. Defina uma senha para
                                    entrar.
                                </div>
                            </div>
                        )}

                        {error && (
                            <div className="notice danger" role="alert">
                                <Icon name="alert" />
                                <div className="small">{error}</div>
                            </div>
                        )}

                        <button
                            className="btn btn-provider btn-block"
                            type="button"
                            onClick={handleGoogle}
                            disabled={submitting}
                        >
                            <GoogleMark />
                            Entrar com conta corporativa
                        </button>

                        {/* TV/tela sem teclado: mostra um QR que o gestor aprova pelo celular já logado. */}
                        <Link className="btn btn-provider btn-block" to="/tv-login">
                            <Icon name="qr" />
                            Entrar com QR Code
                        </Link>

                        <div className="auth-divider" role="separator">
                            <span>ou com e-mail e senha</span>
                        </div>

                        <form className="stack" onSubmit={handleSubmit} noValidate>
                            <div>
                                <label className="lbl" htmlFor="email">
                                    E-mail
                                </label>
                                <div className="field-icon">
                                    <Icon name="mail" size={17} />
                                    <input
                                        className="field"
                                        id="email"
                                        type="email"
                                        autoComplete="username"
                                        placeholder="nome@lexgroup.com.br"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="lbl" htmlFor="senha">
                                    Senha
                                </label>
                                <PasswordInput id="senha" value={password} onChange={setPassword} />
                            </div>
                            <button className="btn btn-primary btn-block" type="submit" disabled={submitting}>
                                {submitting ? 'Entrando…' : 'Entrar'}
                                {!submitting && <Icon name="arrowRight" size={16} />}
                            </button>
                        </form>

                        {/* Entrada só por convite: conta nova sem convite é barrada no Supabase (hook). */}
                        <p className="muted small auth-foot">Ainda não tem acesso? Peça um convite ao administrador.</p>
                    </>
                )}
            </div>
        </main>
    )
}
