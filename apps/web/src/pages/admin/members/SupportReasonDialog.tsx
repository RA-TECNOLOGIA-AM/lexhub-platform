import { useEffect, useId, useRef, useState } from 'react'
import { Modal } from '../../../components/ui/Modal.tsx'
import { REASON_MAX, reasonState } from './supportReason.ts'

type SupportReasonDialogProps = {
    name: string // o membro que será visto
    busy: boolean // iniciando a sessão
    error: string | null // falha ao iniciar (ex.: 403 da API)
    onStart: (reason: string) => void
    onClose: () => void
}

// Módulo: pede o motivo antes de "Ver como este membro" (modo suporte). O motivo vai para a auditoria.
// Esc ou Cancelar fecham; Começar só destrava com 5 a 500 caracteres.
export function SupportReasonDialog({ name, busy, error, onStart, onClose }: SupportReasonDialogProps) {
    const [text, setText] = useState('')
    const fieldId = useId()
    const state = reasonState(text)
    // O <dialog> põe o foco no primeiro botão ao abrir; depois disso, leva para o campo do motivo.
    const field = useRef<HTMLTextAreaElement>(null)
    useEffect(() => field.current?.focus(), [])

    return (
        <Modal
            title={`Ver como ${name}`}
            description="Você vai navegar nos dashboards como esta pessoa vê, só para leitura, por até 1 hora. Fica registrado na auditoria."
            onClose={onClose}
            footer={
                <>
                    <button className="btn" type="button" onClick={onClose}>
                        Cancelar
                    </button>
                    <button
                        className="btn btn-primary"
                        type="button"
                        disabled={busy || !state.ok}
                        onClick={() => onStart(state.reason)}
                    >
                        {busy ? 'Começando…' : 'Começar'}
                    </button>
                </>
            }
        >
            <label className="small" htmlFor={fieldId}>
                Motivo (ex.: número do chamado)
            </label>
            <textarea
                id={fieldId}
                className="field"
                rows={3}
                maxLength={REASON_MAX}
                value={text}
                ref={field}
                onChange={(event) => setText(event.target.value)}
            />
            <span className="muted small">
                {state.length}/{REASON_MAX}
            </span>
            {error && (
                <p className="invite-error" role="alert">
                    {error}
                </p>
            )}
        </Modal>
    )
}
