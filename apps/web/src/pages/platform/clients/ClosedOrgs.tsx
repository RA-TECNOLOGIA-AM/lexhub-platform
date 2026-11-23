import { useState } from 'react'
import { Modal } from '../../../components/ui/Modal.tsx'
import { toDataError } from '../../../services/errors.ts'
import type { ClosedOrg } from '../../../types/index.ts'
import { closedSub } from './clientsView.ts'

type ClosedOrgsProps = {
    orgs: ClosedOrg[]
    onReopen: (org: ClosedOrg) => Promise<void> // se rejeitar, a mensagem aparece no modal
}

// Módulo: as organizações encerradas que ainda dá para reabrir (30 dias), cada uma com "Reabrir" e uma
// confirmação do que volta. Não sabe de API: recebe a lista e o onReopen.
export function ClosedOrgs({ orgs, onReopen }: ClosedOrgsProps) {
    const [confirming, setConfirming] = useState<ClosedOrg | null>(null)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)

    if (orgs.length === 0) return null

    async function reopen() {
        if (!confirming) return
        setSaving(true)
        setError(null)
        try {
            await onReopen(confirming)
            setConfirming(null)
        } catch (err) {
            setError(toDataError(err).message)
        } finally {
            setSaving(false)
        }
    }

    return (
        <section className="card closed-orgs">
            <h2 className="h3" style={{ margin: 0 }}>
                Encerradas
            </h2>
            <p className="muted small" style={{ margin: 0 }}>
                Dá para reabrir por 30 dias. Depois, a organização é apagada de vez com unidades, membros, plano e
                auditoria.
            </p>
            {orgs.map((o) => (
                <div key={o.slug} className="closed-org-row">
                    <span className="stack" style={{ gap: 0 }}>
                        <span style={{ fontWeight: 500 }}>{o.name}</span>
                        <span className="muted small">{closedSub(o)}</span>
                    </span>
                    <button
                        className="btn nowrap"
                        type="button"
                        onClick={() => {
                            setError(null)
                            setConfirming(o)
                        }}
                    >
                        Reabrir
                    </button>
                </div>
            ))}
            {confirming && (
                <Modal
                    title={`Reabrir ${confirming.name}`}
                    className="unit-dialog"
                    onClose={() => setConfirming(null)}
                    footer={
                        <>
                            <button className="btn" type="button" onClick={() => setConfirming(null)} disabled={saving}>
                                Cancelar
                            </button>
                            <button className="btn btn-primary" type="button" onClick={reopen} disabled={saving}>
                                {saving ? 'Reabrindo…' : 'Reabrir organização'}
                            </button>
                        </>
                    }
                >
                    <ul className="delete-impact">
                        <li>Unidades e membros voltam como estavam, e os membros voltam a entrar.</li>
                        <li>As fontes não voltam: foram apagadas com as senhas no encerramento.</li>
                    </ul>
                    {error && (
                        <p className="invite-error" role="alert" style={{ margin: 0 }}>
                            {error}
                        </p>
                    )}
                </Modal>
            )}
        </section>
    )
}
