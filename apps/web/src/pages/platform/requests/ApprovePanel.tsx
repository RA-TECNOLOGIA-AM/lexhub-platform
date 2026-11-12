import { useState, type FormEvent } from 'react'
import { Icon } from '../../../components/ui/Icon.tsx'
import { toDataError } from '../../../services/errors.ts'
import type { AccessRequest, ApprovalOrg, ApprovalTarget, UnitRoleKey } from '../../../types/index.ts'
import { buildTarget, emptyForm, ORG_ROLE_LABEL, slugify, UNIT_ROLES, type ApproveForm } from './approveView.ts'

type ApprovePanelProps = {
    request: AccessRequest
    orgs: ApprovalOrg[]
    onConfirm: (target: ApprovalTarget) => Promise<void> // quem usa decide como aprovar
    onClose: () => void
}

// Módulo: o painel "Aprovar pedido". Guarda o formulário e mostra os avisos; as regras ficam em approveView.ts.
// Organização existente: papel + cargo em cada unidade. Organização nova: nome, endereço e 1ª unidade.
export function ApprovePanel({ request, orgs, onConfirm, onClose }: ApprovePanelProps) {
    const [form, setForm] = useState<ApproveForm>(() => ({
        ...emptyForm(orgs[0]?.id ?? ''),
        newName: request.office,
        newSlug: slugify(request.office),
    }))
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const set = (patch: Partial<ApproveForm>) => setForm((f) => ({ ...f, ...patch }))
    const org = orgs.find((o) => o.id === form.orgId)

    async function submit(e: FormEvent) {
        e.preventDefault()
        const result = buildTarget(form)
        if ('error' in result) return setError(result.error)
        setBusy(true)
        setError(null)
        try {
            await onConfirm(result.target)
        } catch (err) {
            setError(toDataError(err).message)
            setBusy(false)
        }
    }

    return (
        <aside className="card invite" aria-label="Aprovar pedido">
            <form className="stack" style={{ gap: 14 }} onSubmit={submit}>
                <div className="invite-head">
                    <h2 className="h2">Aprovar pedido</h2>
                    <button className="iconbtn" type="button" aria-label="Fechar" onClick={onClose}>
                        <Icon name="close" size={16} />
                    </button>
                </div>
                <p className="small">
                    <strong>{request.full_name}</strong> ({request.email}) · {request.office}
                </p>

                <fieldset className="invite-units">
                    <legend className="lbl">Onde a pessoa entra</legend>
                    <label className="check">
                        <input
                            type="radio"
                            name="mode"
                            checked={form.mode === 'existing'}
                            onChange={() => set({ mode: 'existing' })}
                        />
                        Organização existente
                    </label>
                    <label className="check">
                        <input
                            type="radio"
                            name="mode"
                            checked={form.mode === 'new'}
                            onChange={() => set({ mode: 'new' })}
                        />
                        Organização nova
                    </label>
                </fieldset>

                {form.mode === 'existing' ? (
                    <>
                        <label>
                            <span className="lbl">Organização</span>
                            <select
                                className="field"
                                value={form.orgId}
                                onChange={(e) => set({ orgId: e.target.value, unitRoles: {} })}
                            >
                                {orgs.map((o) => (
                                    <option key={o.id} value={o.id}>
                                        {o.name}
                                    </option>
                                ))}
                            </select>
                        </label>
                        <label>
                            <span className="lbl">Papel na organização</span>
                            <select
                                className="field"
                                value={form.orgRole}
                                onChange={(e) => set({ orgRole: e.target.value as ApproveForm['orgRole'] })}
                            >
                                <option value="member">{ORG_ROLE_LABEL.member}</option>
                                <option value="admin">{ORG_ROLE_LABEL.admin}</option>
                            </select>
                        </label>
                        {form.orgRole === 'member' && org && (
                            <fieldset className="invite-units">
                                <legend className="lbl">Cargo em cada unidade</legend>
                                {org.units.map((u) => (
                                    <label key={u.id} className="row" style={{ justifyContent: 'space-between' }}>
                                        <span className="small">{u.name}</span>
                                        <select
                                            className="field"
                                            style={{ width: 'auto' }}
                                            value={form.unitRoles[u.id] ?? ''}
                                            onChange={(e) =>
                                                set({
                                                    unitRoles: {
                                                        ...form.unitRoles,
                                                        [u.id]: e.target.value as UnitRoleKey | '',
                                                    },
                                                })
                                            }
                                        >
                                            <option value="">Sem acesso</option>
                                            {UNIT_ROLES.map((r) => (
                                                <option key={r.key} value={r.key}>
                                                    {r.label}
                                                </option>
                                            ))}
                                        </select>
                                    </label>
                                ))}
                            </fieldset>
                        )}
                    </>
                ) : (
                    <>
                        <label>
                            <span className="lbl">Nome da organização</span>
                            <input
                                className="field"
                                value={form.newName}
                                onChange={(e) => set({ newName: e.target.value, newSlug: slugify(e.target.value) })}
                            />
                        </label>
                        <label>
                            <span className="lbl">Endereço (lexhub.app/…)</span>
                            <input
                                className="field"
                                value={form.newSlug}
                                onChange={(e) => set({ newSlug: e.target.value })}
                            />
                        </label>
                        <label>
                            <span className="lbl">Papel da pessoa</span>
                            <select
                                className="field"
                                value={form.newRole}
                                onChange={(e) => set({ newRole: e.target.value as ApproveForm['newRole'] })}
                            >
                                <option value="owner">{ORG_ROLE_LABEL.owner}</option>
                                <option value="admin">{ORG_ROLE_LABEL.admin}</option>
                            </select>
                        </label>
                        <div className="row" style={{ alignItems: 'flex-end' }}>
                            <label style={{ flex: '0 0 110px' }}>
                                <span className="lbl">Código</span>
                                <input
                                    className="field"
                                    placeholder="SEDE"
                                    value={form.unitCode}
                                    onChange={(e) => set({ unitCode: e.target.value.toUpperCase() })}
                                />
                            </label>
                            <label style={{ flex: '1 1 140px' }}>
                                <span className="lbl">1ª unidade</span>
                                <input
                                    className="field"
                                    placeholder="Sede"
                                    value={form.unitName}
                                    onChange={(e) => set({ unitName: e.target.value })}
                                />
                            </label>
                        </div>
                    </>
                )}

                {error && (
                    <p className="invite-error" role="alert">
                        {error}
                    </p>
                )}
                <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
                    {busy ? 'Aprovando…' : 'Aprovar e liberar acesso'}
                </button>
                <span className="muted small" style={{ textAlign: 'center' }}>
                    Fica registrado na auditoria.
                </span>
            </form>
        </aside>
    )
}
