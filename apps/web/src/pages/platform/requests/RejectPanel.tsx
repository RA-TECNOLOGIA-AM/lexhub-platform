import { useState, type FormEvent } from 'react'
import { Icon } from '../../../components/ui/Icon.tsx'
import { toDataError } from '../../../services/errors.ts'
import type { AccessRequest } from '../../../types/index.ts'

type RejectPanelProps = {
    request: AccessRequest
    onConfirm: (note: string | null) => Promise<void> // quem usa decide como recusar
    onClose: () => void
}

// Módulo: o painel "Recusar pedido", com uma nota opcional que a pessoa vê no card de sem acesso.
export function RejectPanel({ request, onConfirm, onClose }: RejectPanelProps) {
    const [note, setNote] = useState('')
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)

    async function submit(e: FormEvent) {
        e.preventDefault()
        setBusy(true)
        setError(null)
        try {
            await onConfirm(note.trim() || null)
        } catch (err) {
            setError(toDataError(err).message)
            setBusy(false)
        }
    }

    return (
        <aside className="card invite" aria-label="Recusar pedido">
            <form className="stack" style={{ gap: 14 }} onSubmit={submit}>
                <div className="invite-head">
                    <h2 className="h2">Recusar pedido</h2>
                    <button className="iconbtn" type="button" aria-label="Fechar" onClick={onClose}>
                        <Icon name="close" size={16} />
                    </button>
                </div>
                <p className="small">
                    <strong>{request.full_name}</strong> ({request.email}) · {request.office}
                </p>
                <label>
                    <span className="lbl">
                        Nota para a pessoa <span className="muted">(opcional)</span>
                    </span>
                    <textarea
                        className="field"
                        rows={3}
                        maxLength={500}
                        placeholder="Ex.: não encontramos o seu escritório entre os clientes"
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                    />
                </label>
                {error && (
                    <p className="invite-error" role="alert">
                        {error}
                    </p>
                )}
                <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
                    {busy ? 'Recusando…' : 'Recusar pedido'}
                </button>
            </form>
        </aside>
    )
}
