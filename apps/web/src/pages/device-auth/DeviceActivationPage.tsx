import { useEffect, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router'
import { DataError } from '../../services/errors.ts'
import { dataClient } from '../../services/client.ts'

const USER_CODE = /^[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}$/

export function DeviceActivationPage() {
    const [params] = useSearchParams()
    const location = useLocation()
    const navigate = useNavigate()
    const [code, setCode] = useState(params.get('code') ?? '')
    const [checkingSession, setCheckingSession] = useState(true)
    const [submitting, setSubmitting] = useState(false)
    const [authorized, setAuthorized] = useState(false)
    const [error, setError] = useState('')

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
        const normalized = code.trim().toUpperCase()
        if (!USER_CODE.test(normalized)) {
            setError('Digite o código no formato ABCD-EFGH.')
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
            setError(reason instanceof DataError ? reason.message : 'Não foi possível autorizar a TV.')
        } finally {
            setSubmitting(false)
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
                                maxLength={9}
                                placeholder="ABCD-EFGH"
                                value={code}
                                onChange={(event) => setCode(event.target.value.toUpperCase())}
                                disabled={submitting}
                            />
                        </div>
                        {error && (
                            <div className="notice danger" role="alert">
                                {error}
                            </div>
                        )}
                        <button className="btn btn-primary btn-block" type="submit" disabled={submitting}>
                            {submitting ? 'Autorizando…' : 'Autorizar TV'}
                        </button>
                    </form>
                )}

                <p className="muted small auth-foot">
                    <Link className="linkbtn" to="/">
                        Voltar ao LexHub
                    </Link>
                </p>
            </section>
        </main>
    )
}
