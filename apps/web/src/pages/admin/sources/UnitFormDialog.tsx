import { useState } from 'react'
import type { UnitInput } from '../../../types/index.ts'
import { Modal } from '../../../components/ui/Modal.tsx'
import { toDataError } from '../../../services/errors.ts'
import { BR_TIMEZONES, normalizeCode, suggestCode, validateUnit } from './unitForm.ts'

type UnitFormDialogProps = {
    mode: 'create' | 'edit'
    initial?: UnitInput // edição: a unidade como está
    existingCodes: string[] // para avisar código repetido antes de enviar
    onSave: (unit: UnitInput) => Promise<void> // grava; se rejeitar, a mensagem aparece no modal
    onClose: () => void
}

const EMPTY: UnitInput = { code: '', name: '', timezone: 'America/Manaus' }

// Módulo: o formulário de unidade num modal — criar (nome, código, fuso) ou editar (nome, fuso; o código não muda).
// Não sabe de API: recebe onSave e mostra o erro que ele devolver.
export function UnitFormDialog({ mode, initial, existingCodes, onSave, onClose }: UnitFormDialogProps) {
    const [draft, setDraft] = useState<UnitInput>(initial ?? EMPTY)
    // Enquanto a pessoa não mexe no código, ele acompanha o nome.
    const [codeTouched, setCodeTouched] = useState(mode === 'edit')
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)

    async function save() {
        const problem = validateUnit(draft, mode, existingCodes)
        if (problem) {
            setError(problem)
            return
        }
        setSaving(true)
        setError(null)
        try {
            await onSave({ ...draft, name: draft.name.trim() })
            onClose()
        } catch (err) {
            setError(toDataError(err).message)
            setSaving(false)
        }
    }

    return (
        <Modal
            title={mode === 'create' ? 'Nova unidade' : `Editar ${initial?.name ?? 'unidade'}`}
            subtitle={mode === 'create' ? 'A unidade nasce sem fontes; elas são ligadas depois.' : undefined}
            className="unit-dialog"
            onClose={onClose}
            footer={
                <>
                    <button className="btn" type="button" onClick={onClose} disabled={saving}>
                        Cancelar
                    </button>
                    <button className="btn btn-primary" type="button" onClick={save} disabled={saving}>
                        {saving ? 'Salvando…' : mode === 'create' ? 'Criar unidade' : 'Salvar'}
                    </button>
                </>
            }
        >
            <label>
                <span className="lbl">Nome</span>
                <input
                    className="field"
                    value={draft.name}
                    placeholder="Luis Albert SP"
                    onChange={(e) =>
                        setDraft({
                            ...draft,
                            name: e.target.value,
                            code: codeTouched ? draft.code : suggestCode(e.target.value),
                        })
                    }
                />
            </label>
            <label>
                <span className="lbl">Código</span>
                <input
                    className="field"
                    value={draft.code}
                    disabled={mode === 'edit'}
                    placeholder="LASP"
                    onChange={(e) => {
                        setCodeTouched(true)
                        setDraft({ ...draft, code: normalizeCode(e.target.value) })
                    }}
                />
                <span className="muted small">
                    {mode === 'edit'
                        ? 'O código não muda: as fontes e os endereços usam ele.'
                        : 'De 2 a 16 letras maiúsculas, números ou _. Não muda depois.'}
                </span>
            </label>
            <label>
                <span className="lbl">Fuso</span>
                <select
                    className="field"
                    value={draft.timezone}
                    onChange={(e) => setDraft({ ...draft, timezone: e.target.value })}
                >
                    {BR_TIMEZONES.map((t) => (
                        <option key={t.tz} value={t.tz}>
                            {t.label}
                        </option>
                    ))}
                </select>
                <span className="muted small">Define o corte de "hoje" e "mês" nos dashboards da unidade.</span>
            </label>
            {error && (
                <p className="invite-error" role="alert" style={{ margin: 0 }}>
                    {error}
                </p>
            )}
        </Modal>
    )
}
