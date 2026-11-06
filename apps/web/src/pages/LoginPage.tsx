import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useSearchParams } from 'react-router'
import { useAuth } from '../auth/auth-context.ts'
import { Icon } from '../components/Icon.tsx'
import { DataError } from '../data/errors.ts'

// MVP: e-mail + senha e entrada por convite (?convite=<token>). Google e MFA ficam para depois.
// ?estado=sessao-expirada = veio de um 401 da API.
export function LoginPage() {
    const { me, signIn } = useAuth()
    const location = useLocation()
    const [params] = useSearchParams()
    const invite = params.get('convite')

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [submitting, setSubmitting] = useState(false)
    const [error, setError] = useState(
        params.get('estado') === 'sessao-expirada' ? 'Sua sessão expirou. Entre de novo para continuar.' : '',
    )

    // Logado (já estava, ou acabou de entrar): volta para onde queria ir, ou para o hub.
    if (me) {
        const from = (location.state as { from?: string } | null)?.from
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
            setSubmitting(false)
        }
    }

    return (
        <main className="auth">
            <div className="card auth-card">
                <div className="brand">
                    <span className="brand-mark">LH</span>
                    <span>LexHub</span>
                </div>
                <div className="stack" style={{ gap: 4 }}>
                    <h1 className="h1" style={{ fontSize: 22 }}>
                        {invite ? 'Aceitar convite' : 'Entrar'}
                    </h1>
                    <p className="muted small">Use o e-mail da sua organização.</p>
                </div>

                {invite && (
                    <div className="notice info">
                        <Icon name="info" />
                        <div className="small">
                            Você foi convidado para <strong>LexGroup · NG</strong>. Defina uma senha para entrar.
                        </div>
                    </div>
                )}

                {error && (
                    <div className="notice danger" role="alert">
                        <Icon name="alert" />
                        <div className="small">{error}</div>
                    </div>
                )}

                <form className="stack" onSubmit={handleSubmit} noValidate>
                    <div>
                        <label className="lbl" htmlFor="email">
                            E-mail
                        </label>
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
                    <div>
                        <label className="lbl" htmlFor="senha">
                            Senha
                        </label>
                        <input
                            className="field"
                            id="senha"
                            type="password"
                            autoComplete="current-password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                    <button className="btn btn-primary" type="submit" style={{ width: '100%' }} disabled={submitting}>
                        {submitting ? 'Entrando…' : 'Entrar'}
                    </button>
                </form>

                <p className="muted small">Sem acesso? Peça um convite ao gestor da sua unidade.</p>
            </div>
        </main>
    )
}