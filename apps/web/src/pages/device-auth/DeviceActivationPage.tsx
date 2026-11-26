import { useEffect, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router'
import { DataError } from '../../services/errors.ts'
import { dataClient } from '../../services/client.ts'
import { Icon } from '../../components/ui/Icon.tsx'
import { formatUserCode, normalizeUserCode } from './userCode.ts'

export function DeviceActivationPage() {
    const [params] = useSearchParams()
    const location = useLocation()
    const navigate = useNavigate()
    const [code, setCode] = useState(formatUserCode(params.get('code') ?? ''))
    const [checkingSession, setCheckingSession] = useState(true)
    const [submitting, setSubmitting] = useState(false)
    const [authorized, setAuthorized] = useState(false)
    const [error, setError] = useState('')
    // Contra phishing: quem autoriza confirma que vê a TV. Link recebido de outra pessoa = sessão entregue a ela.
    const [atTv, setAtTv] = useState(false)
    // Desconectar outros aparelhos: idle -> confirm (pergunta) -> working -> done.
    const [others, setOthers] = useState<'idle' | 'confirm' | 'working' | 'done'>('idle')

    useEffect(() => {
        let cancelled = false
        void dataClient
            .getSessionAccessToken()
            .then((token) => {
                if (cancelled) return
                if (!token) {
                    const returnTo = `${location.pathname}${location.search}`
                    navigate(`/login?returnTo=${encodeURIComponent(returnTo)}`, { replace: true })
                    return
                }
                setCheckingSession(false)
            })
            .catch((reason: unknown) => {
                if (cancelled) return
                setError(reason instanceof DataError ? reason.message : 'Não foi possível conferir sua sessão.')
                setCheckingSession(false)
            })
        return () => {
            cancelled = true
        }
    }, [location.pathname, location.search, navigate])

    async function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault()
        const normalized = normalizeUserCode(code)
        if (!normalized) {
            setError('Digite os 8 caracteres do código que aparece na TV.')
            return
        }
        if (!atTv) {
            setError('Confirme que você está na frente da TV que mostra este código.')
            return
        }

        setError('')
        setSubmitting(true)
        try {
            await dataClient.authorizeDevice(normalized)
            setAuthorized(true)
            setCode('')
            navigate('/ativar', { replace: true })
        } catch (reason) {
            // Sessão deste celular já foi encerrada no servidor (o token local ainda parecia válido):
            // entra de novo e volta para cá com o mesmo código, em vez de travar no erro.
            if (reason instanceof DataError && reason.status === 401) {
                await dataClient.signOut().catch(() => {})
                const returnTo = `/ativar?${new URLSearchParams({ code: normalized })}`
                navigate(`/login?returnTo=${encodeURIComponent(returnTo)}`, { replace: true })
                return
            }
            setError(reason instanceof DataError ? reason.message : 'Não foi possível autorizar a TV.')
        } finally {
            setSubmitting(false)
        }
    }

    async function disconnectOthers() {
        setOthers('working')
        try {
            await dataClient.signOutOthers()
            setOthers('done')
        } catch (reason) {
            setOthers('idle')
            setError(reason instanceof DataError ? reason.message : 'Não foi possível desconectar os outros aparelhos.')
        }
    }

    if (checkingSession) {
        return (
            <main className="auth">
                <div className="card auth-card" role="status">
                    Conferindo sua sessão…
                </div>
            </main>
        )
    }

    return (
        <main className="auth">
            <section className="card auth-card">
                <div className="stack" style={{ gap: 6 }}>
                    <h1 className="h1" style={{ fontSize: 24 }}>
                        {authorized ? 'TV autorizada' : 'Ativar uma TV'}
                    </h1>
                    <p className="muted small">
                        {authorized
                            ? 'Você já pode voltar à TV. O login foi concluído com segurança.'
                            : 'Confirme o código mostrado na tela da TV para entrar na sua conta.'}
                    </p>
                </div>

                {!authorized && (
                    <form className="stack" onSubmit={(event) => void submit(event)} noValidate>
                        <div>
                            <label className="lbl" htmlFor="device-code">
                                Código da TV
                            </label>
                            <input
                                className="field"
                                id="device-code"
                                autoComplete="one-time-code"
                                autoCapitalize="characters"
                                placeholder="ABCD-EFGH"
                                value={code}
                                onChange={(event) => setCode(formatUserCode(event.target.value))}
                                disabled={submitting}
                            />
                        </div>
                        <div className="notice" role="note">
                            <span>
                                A TV vai entrar na <strong>sua conta</strong>. Só autorize se você está vendo esse
                                código agora numa TV da LexGroup. Se recebeu este link por mensagem ou e-mail, não
                                autorize.
                            </span>
                        </div>
                        <label className="small" style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                            <input
                                type="checkbox"
                                checked={atTv}
                                onChange={(event) => setAtTv(event.target.checked)}
                                disabled={submitting}
                            />
                            <span>Estou na frente da TV e o código acima é o mesmo que aparece nela.</span>
                        </label>
                        {error && (
                            <div className="notice danger" role="alert">
                                {error}
                            </div>
                        )}
                        <button className="btn btn-primary btn-block" type="submit" disabled={submitting || !atTv}>
                            {submitting ? 'Autorizando…' : 'Autorizar TV'}
                        </button>
                    </form>
                )}

                {/* TV esquecida logada: derruba as sessões dos outros aparelhos (este continua). */}
                <div className="stack" style={{ gap: 8, borderTop: '1px solid var(--border)', paddingTop: 14 }}>
                    {others === 'done' ? (
                        <p className="muted small" role="status">
                            Pronto. Os outros aparelhos saem da sua conta em até 1 minuto; as TVs voltam para o QR Code.
                        </p>
                    ) : others === 'idle' ? (
                        <button className="btn btn-block" type="button" onClick={() => setOthers('confirm')}>
                            <Icon name="logout" size={16} />
                            Desconectar outros aparelhos
                        </button>
                    ) : (
                        <>
                            <p className="muted small">
                                Sua conta sai de todos os outros lugares onde está aberta: TVs, computadores e
                                celulares. Só este aparelho continua conectado.
                            </p>
                            <div className="row" style={{ gap: 8 }}>
                                <button
                                    className="btn"
                                    type="button"
                                    onClick={() => setOthers('idle')}
                                    disabled={others === 'working'}
                                >
                                    Cancelar
                                </button>
                                <button
                                    className="btn btn-primary"
                                    type="button"
                                    onClick={() => void disconnectOthers()}
                                    disabled={others === 'working'}
                                >
                                    {others === 'working' ? 'Desconectando…' : 'Desconectar'}
                                </button>
                            </div>
                        </>
                    )}
                </div>

                <p className="muted small auth-foot">
                    <Link className="linkbtn" to="/">
                        Voltar ao LexHub
                    </Link>
                </p>
            </section>
        </main>
    )
}
