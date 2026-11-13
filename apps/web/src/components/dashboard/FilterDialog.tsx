import { useState } from 'react'
import { Modal } from '../ui/Modal.tsx'
import { toggleFilter, type FilterField } from '../../lib/filters.ts'
import type { DashboardFilters } from '../../types/index.ts'

type FilterDialogProps = {
    fields: FilterField[] // os filtros que o dashboard oferece ([] = nenhum)
    value: DashboardFilters // os filtros em uso (vêm da URL)
    onApply: (filters: DashboardFilters) => void
    onClose: () => void
}

// Módulo: a janela "Filtros". Edita um rascunho e só muda a URL no Aplicar.
// Usa o Modal da casa (como a de Exportar): prende o foco, fecha com Esc e escurece o fundo.
// Quem usa só a desenha quando está aberta.
export function FilterDialog({ fields, value, onApply, onClose }: FilterDialogProps) {
    const [draft, setDraft] = useState<DashboardFilters>(value)

    function apply() {
        onApply(draft)
        onClose()
    }

    return (
        <Modal
            title="Filtros"
            onClose={onClose}
            footer={
                <>
                    {fields.length > 0 && (
                        <button className="btn" type="button" onClick={() => setDraft({})}>
                            Limpar
                        </button>
                    )}
                    <button className="btn" type="button" onClick={onClose}>
                        Cancelar
                    </button>
                    {fields.length > 0 && (
                        <button className="btn btn-primary" type="button" onClick={apply}>
                            Aplicar
                        </button>
                    )}
                </>
            }
        >
            {fields.length === 0 ? (
                <p className="muted small" style={{ margin: 0 }}>
                    Este dashboard ainda não tem filtros.
                </p>
            ) : (
                fields.map((field) => (
                    <fieldset key={field.key} className="filter-group">
                        <legend className="export-group-title">{field.label}</legend>
                        <div className="export-fields">
                            {field.options.map((option) => (
                                <label key={option.value} className="check">
                                    <input
                                        type="checkbox"
                                        checked={draft[field.key]?.includes(option.value) ?? false}
                                        onChange={() => setDraft(toggleFilter(draft, field.key, option.value))}
                                    />
                                    {option.label}
                                </label>
                            ))}
                        </div>
                    </fieldset>
                ))
            )}
        </Modal>
    )
}
