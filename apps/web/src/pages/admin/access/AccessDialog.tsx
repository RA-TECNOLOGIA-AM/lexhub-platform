import { useState } from 'react'
import { Modal } from '../../../components/ui/Modal.tsx'
import { toDataError } from '../../../services/errors.ts'
import type { AccessOverview, Member, MemberAccessUpdate, UnitRoleKey } from '../../../types/index.ts'
import { ROLE_LABEL } from '../members/memberView.ts'
import {
    draftFromMember,
    isDirty,
    previewDashboards,
    previewText,
    readOnlyReason,
    setUnitRole,
    toggleTeam,
    toUpdate,
} from './accessEditor.ts'

type AccessDialogProps = {
    member: Member
    overview: AccessOverview
    isSelf: boolean
    onSave: (update: MemberAccessUpdate) => Promise<void>
    onClose: () => void
}

const UNIT_ROLES: UnitRoleKey[] = ['gestor', 'controller', 'colaborador', 'leitor']

// Módulo: a janela de acesso de uma pessoa — cargo por unidade, equipes e (Owner/Dev) Desenvolvedor,
// com a prévia do que ela passa a ver. Edita um rascunho; nada muda até o Salvar. Cancelar (ou Esc)
// fecha sem gravar. Usa o Modal da casa, como Filtros e Exportar.
export function AccessDialog({ member, overview, isSelf, onSave, onClose }: AccessDialogProps) {
    const [original] = useState(() => draftFromMember(member, overview))
    const [draft, setDraft] = useState(original)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)

    async function save() {
        setSaving(true)
        setError(null)
        try {
            await onSave(toUpdate(draft, original, overview.can_set_org_role))
            onClose()
        } catch (err) {
            setError(toDataError(err).message)
            setSaving(false)
        }
    }

    // Gestor não edita Owner/Desenvolvedor nem o próprio acesso (o banco também recusa).
    const readOnlyText = readOnlyReason(member, overview, isSelf)
    const readOnly = readOnlyText !== null
    const dirty = isDirty(original, draft)
    const unitName = (code: string) => overview.units.find((u) => u.code === code)?.name ?? code
    const preview = previewDashboards(overview, draft)

    return (
        <Modal
            title={member.name}
            subtitle={member.email}
            className="access-dialog"
            onClose={onClose}
            footer={
                <>
                    <button className="btn" type="button" onClick={onClose} disabled={saving}>
                        {dirty ? 'Cancelar' : 'Fechar'}
                    </button>
                    {!readOnly && (
                        <button className="btn btn-primary" type="button" disabled={!dirty || saving} onClick={save}>
                            {saving ? 'Salvando…' : 'Salvar'}
                        </button>
                    )}
                </>
            }
        >
            {readOnly && (
                <p className="muted small" style={{ margin: 0 }}>
                    {readOnlyText}
                </p>
            )}
            {overview.can_set_org_role && member.org_role !== 'owner' && (
                <label className="check">
                    <input
                        type="checkbox"
                        checked={draft.orgRole === 'admin'}
                        disabled={isSelf}
                        onChange={(e) => setDraft({ ...draft, orgRole: e.target.checked ? 'admin' : 'member' })}
                    />
                    Desenvolvedor — vê e gere todas as unidades
                    {isSelf && <span className="muted small">(você não muda o próprio papel)</span>}
                </label>
            )}

            <div className="unit-grid">
                {overview.units.map((u) => {
                    const role = draft.units[u.code] ?? ''
                    const unitTeams = overview.teams.filter((t) => t.unit === u.code)
                    return (
                        <fieldset key={u.code} className="unit-card">
                            <legend className="export-group-title">{u.name}</legend>
                            <select
                                className="field"
                                aria-label={`Cargo em ${u.name}`}
                                value={role}
                                disabled={readOnly}
                                onChange={(e) =>
                                    setDraft(
                                        setUnitRole(draft, u.code, e.target.value as UnitRoleKey | '', overview.teams),
                                    )
                                }
                            >
                                <option value="">Sem cargo</option>
                                {UNIT_ROLES.map((r) => (
                                    <option key={r} value={r}>
                                        {ROLE_LABEL[r]}
                                    </option>
                                ))}
                            </select>
                            {role && unitTeams.length > 0 && (
                                <div className="unit-teams">
                                    {unitTeams.map((t) => (
                                        <label key={t.id} className="check">
                                            <input
                                                type="checkbox"
                                                checked={draft.teams.includes(t.id)}
                                                disabled={readOnly}
                                                onChange={() => setDraft(toggleTeam(draft, t.id))}
                                            />
                                            {t.name}
                                        </label>
                                    ))}
                                </div>
                            )}
                            {role && unitTeams.length === 0 && (
                                <span className="muted small">Nenhuma equipe nesta unidade.</span>
                            )}
                        </fieldset>
                    )
                })}
            </div>

            <div className="invite-preview stack" style={{ gap: 6 }} aria-live="polite">
                <span style={{ fontWeight: 500 }}>O que passa a ver</span>
                {preview.length === 0 && <span>Nenhum dashboard: sem cargo em nenhuma unidade.</span>}
                {preview.map((p) => (
                    <span key={p.unit}>
                        <strong>{unitName(p.unit)}</strong>: {previewText(p)}
                    </span>
                ))}
            </div>

            {error && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {error}
                </p>
            )}
        </Modal>
    )
}
