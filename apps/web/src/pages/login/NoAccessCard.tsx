import { useEffect, useState, type FormEvent } from 'react'
import { Icon } from '../../components/ui/Icon.tsx'
import { useAuth } from '../../contexts/auth-context.ts'
import { dataClient } from '../../services/client.ts'
import { toDataError } from '../../services/errors.ts'
import type { AccessRequest } from '../../types/index.ts'
import { MESSAGE_MAX, OFFICE_MAX, requestDate, stepOf, validateRequest } from './noAccessView.ts'

type NoAccessCardProps = {
    email: string | null
    onSignOut: () => void
}

// O miolo do card de login para quem entrou (ex.: com o Google) mas não está em nenhuma organização.
// Busca o último pedido e mostra: formulário (sem pedido), aguardando (pendente) ou recusado.
// A aprovação é feita pela equipe RA em Plataforma > Pedidos de acesso.
export function NoAccessCard({ email, onSignOut }: NoAccessCardProps) {
    const { refreshSession } = useAuth()
    const [request, setRequest] = useState<AccessRequest | null | undefined>(undefined) // undefined = carregando
    const [asking, setAsking] = useState(false) // "Pedir de novo" depois de uma recusa
    const [office, setOffice] = useState('')
    const [message, setMessage] = useState('')
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        let ignore = false
        dataClient
            .getMyAccessRequest()
            .then((found) => !ignore && setRequest(found))
            .catch((err) => {
                if (ignore) return
                setRequest(null)
                setError(toDataError(err).message)
            })
        return () => {
            ignore = true
        }
    }, [])

    async function send(e: FormEvent) {
        e.preventDefault()
        const invalid = validateRequest(office, message)
        if (invalid) return setError(invalid)
        setBusy(true)
        setError(null)
        try {
            setRequest(await dataClient.requestAccess(office.trim(), message.trim() || null))
            setAsking(false)
        } catch (err) {
            setError(toDataError(err).message)
        } finally {
            setBusy(false)
        }
    }

    // Aprovado: o refreshSession preenche o "me" e o login leva ao hub. Senão, continua aqui.
    async function checkAgain() {
        setBusy(true)
        setError(null)
        try {
            await refreshSession()
            setRequest(await dataClient.getMyAccessRequest())
        } catch (err) {
            setError(toDataError(err).message)
        } finally {
            setBusy(false)
        }
    }

    const step = asking ? 'form' : request === undefined ? null : stepOf(request)

    return (
        <>
            <div className="stack" style={{ gap: 6 }}>
                <h1 className="h1" style={{ fontSize: 22 }}>
                    Você ainda não tem acesso
                </h1>
                <p className="muted small">
                    {email ? (
                        <>
                            Você entrou como <strong>{email}</strong>, mas essa conta ainda não faz parte de nenhuma
                            organização no LexHub.
                        </>
                    ) : (
                        'Sua conta ainda não faz parte de nenhuma organização no LexHub.'
                    )}
                </p>
            </div>

            {error && (
                <div className="notice danger" role="alert">
                    <Icon name="alert" />
                    <div className="small">{error}</div>
                </div>
            )}

            {step === null && <p className="muted small">Carregando…</p>}

            {step === 'form' && (
                <form className="stack" onSubmit={send} noValidate>
                    <div>
                        <label className="lbl" htmlFor="office">
                            Escritório ou empresa
                        </label>
                        <input
                            className="field"
                            id="office"
                            maxLength={OFFICE_MAX}
                            placeholder="Ex.: Nicolas Gomes Advocacia"
                            value={office}
                            onChange={(e) => setOffice(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="lbl" htmlFor="message">
                            Mensagem <span className="muted">(opcional)</span>
                        </label>
                        <textarea
                            className="field"
                            id="message"
                            rows={3}
                            maxLength={MESSAGE_MAX}
                            placeholder="Seu setor e o que precisa acessar"
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                        />
                    </div>
                    <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
                        {busy ? 'Enviando…' : 'Solicitar acesso'}
                    </button>
                </form>
            )}

            {step === 'pending' && request && (
                <>
                    <div className="notice info">
                        <Icon name="clock" />
                        <div className="small">
                            Pedido enviado em <strong>{requestDate(request.created_at)}</strong> ({request.office}).
                            Aguardando aprovação da equipe do LexHub.
                        </div>
                    </div>
                    <button className="btn btn-primary btn-block" type="button" onClick={checkAgain} disabled={busy}>
                        {busy ? 'Verificando…' : 'Verificar de novo'}
                    </button>
                </>
            )}

            {step === 'rejected' && request && (
                <>
                    <div className="notice warn">
                        <Icon name="alert" />
                        <div className="small">
                            Seu pedido de {requestDate(request.created_at)} não foi aprovado
                            {request.decision_note ? (
                                <>
                                    : <em>{request.decision_note}</em>
                                </>
                            ) : (
                                '.'
                            )}
                        </div>
                    </div>
                    <button className="btn btn-primary btn-block" type="button" onClick={() => setAsking(true)}>
                        Pedir de novo
                    </button>
                </>
            )}

            <button className="btn btn-block" type="button" onClick={onSignOut}>
                <Icon name="logout" size={16} />
                Usar outra conta
            </button>
        </>
    )
}
