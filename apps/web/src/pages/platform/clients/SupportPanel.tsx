import { useState, type FormEvent } from 'react'
import { Icon } from '../../../components/ui/Icon.tsx'
import { validateSupportReason } from './clientsView.ts'

type SupportPanelProps = {
    orgName: string
    onConfirm: (reason: string) => void // motivo já validado
    onClose: () => void
}

// Módulo: o painel "Sessão de suporte em X". Pede o motivo, mostra as regras e valida antes de confirmar.
export function SupportPanel({ orgName, onConfirm, onClose }: SupportPanelProps) {
    const [reason, setReason] = useState('')
    const [error, setError] = useState<string | null>(null)

    function submit(e: FormEvent) {
        e.preventDefault()
        const problem = validateSupportReason(reason)
        if (problem) return setError(problem)
        onConfirm(reason.trim())
    }

    return (
        <form className="card stack support-panel" aria-label="Iniciar sessão de suporte" onSubmit={submit}>
            <div className="invite-head">
                <h2 className="h2">Sessão de suporte em {orgName}</h2>
                <button className="iconbtn" type="button" aria-label="Fechar" onClick={onClose}>
                    <Icon name="close" size={16} />
                </button>
            </div>
            <label>
                <span className="lbl">Motivo (fica visível para o cliente)</span>
                <textarea
                    className="field"
                    rows={2}
                    placeholder="Conferir divergência no dashboard de Protocolo, chamado #[NÚMERO]"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    aria-invalid={error !== null}
                />
            </label>
            {error && (
                <p className="invite-error" role="alert">
                    {error}
                </p>
            )}
            <ul className="support-rules">
                <li>Somente leitura: nada pode ser alterado nem exportado.</li>
                <li>Expira em 1 hora e pede confirmação por MFA.</li>
                <li>Aparece na auditoria do cliente, com o motivo.</li>
            </ul>
            <div className="row" style={{ justifyContent: 'flex-end', gap: 8 }}>
                <button className="btn" type="button" onClick={onClose}>
                    Cancelar
                </button>
                <button className="btn btn-primary" type="submit">
                    Confirmar com MFA
                </button>
            </div>
        </form>
    )
}
