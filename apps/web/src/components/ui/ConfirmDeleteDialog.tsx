import { useState } from 'react'
import { Modal } from './Modal.tsx'
import { toDataError } from '../../services/errors.ts'

// O que a tela mostra antes de confirmar. null = ainda carregando.
export type DeleteImpact = {
    items: string[] // "2 fontes desligadas e senhas apagadas", "5 dashboards deixam de aparecer"...
    blocked: string | null // por que não pode (trava, última unidade); null = pode
    note?: string // depois da lista ("Volta em até 30 dias pelo suporte.")
}

type ConfirmDeleteDialogProps = {
    title: string // "Excluir Escritório de Teste"
    name: string // o que a pessoa digita para confirmar
    nameLabel: string // "o nome da unidade"
    confirmLabel: string // "Excluir unidade"
    impact: DeleteImpact | null
    loadError?: string | null // não deu para buscar o impacto
    onConfirm: (typedName: string) => Promise<void> // se rejeitar, a mensagem aparece no modal
    onClose: () => void
}

// Módulo: confirmação de exclusão — mostra o que vai junto, pede para digitar o nome e só então libera o
// botão. Não sabe o que exclui: recebe o impacto já em texto e o onConfirm (o servidor confere tudo de novo).
export function ConfirmDeleteDialog({
    title,
    name,
    nameLabel,
    confirmLabel,
    impact,
    loadError,
    onConfirm,
    onClose,
}: ConfirmDeleteDialogProps) {
    const [typed, setTyped] = useState('')
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const matches = typed.trim().toLowerCase() === name.trim().toLowerCase()
    const ready = impact !== null && impact.blocked === null && matches && !saving

    async function confirm() {
        setSaving(true)
        setError(null)
        try {
            await onConfirm(typed)
            onClose()
        } catch (err) {
            setError(toDataError(err).message)
            setSaving(false)
        }
    }

    return (
        <Modal
            title={title}
            className="unit-dialog"
            onClose={onClose}
            footer={
                <>
                    <button className="btn" type="button" onClick={onClose} disabled={saving}>
                        Cancelar
                    </button>
                    {!impact?.blocked && (
                        <button className="btn btn-danger solid" type="button" onClick={confirm} disabled={!ready}>
                            {saving ? 'Excluindo…' : confirmLabel}
                        </button>
                    )}
                </>
            }
        >
            {loadError && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {loadError}
                </p>
            )}
            {!impact && !loadError && <p className="muted small">Calculando o que vai junto…</p>}
            {impact?.blocked && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {impact.blocked}
                </p>
            )}
            {impact && !impact.blocked && (
                <>
                    <div className="connect-confirm">
                        <strong>Vai junto:</strong>
                        <ul className="delete-impact">
                            {impact.items.map((item) => (
                                <li key={item}>{item}</li>
                            ))}
                        </ul>
                        {impact.note && <span className="muted small">{impact.note}</span>}
                    </div>
                    <label>
                        <span className="lbl">
                            Para confirmar, digite {nameLabel}: <strong>{name}</strong>
                        </span>
                        <input
                            className="field"
                            value={typed}
                            autoComplete="off"
                            autoFocus
                            onChange={(e) => setTyped(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && ready) void confirm()
                            }}
                        />
                    </label>
                </>
            )}
            {error && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {error}
                </p>
            )}
        </Modal>
    )
}
