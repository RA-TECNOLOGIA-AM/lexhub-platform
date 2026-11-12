import { useEffect, useRef, useState } from 'react'
import { Icon } from '../ui/Icon.tsx'
import { toggleFilter, type FilterField } from '../../lib/filters.ts'
import type { DashboardFilters } from '../../types/index.ts'

type FilterDialogProps = {
    fields: FilterField[] // os filtros que o dashboard oferece ([] = nenhum)
    value: DashboardFilters // os filtros em uso (vêm da URL)
    onApply: (filters: DashboardFilters) => void
    onClose: () => void
}

// Módulo: a janela "Filtros". Edita um rascunho e só muda a URL no Aplicar.
// Usa o <dialog> do navegador (como a de Exportar): prende o foco, fecha com Esc e escurece o fundo.
// Quem usa só a desenha quando está aberta.
export function FilterDialog({ fields, value, onApply, onClose }: FilterDialogProps) {
    const dialog = useRef<HTMLDialogElement>(null)
    const [draft, setDraft] = useState<DashboardFilters>(value)

    useEffect(() => {
        dialog.current?.showModal()
    }, [])

    // Fecha o <dialog> antes de sumir com ele: o navegador libera a página e devolve o foco ao botão.
    function close() {
        dialog.current?.close()
        onClose()
    }

    function apply() {
        onApply(draft)
        close()
    }

    return (
        <dialog
            ref={dialog}
            className="export-dialog"
            aria-labelledby="filter-title"
            onCancel={(event) => {
                event.preventDefault()
                close()
            }}
        >
            <div className="export-head">
                <div className="row" style={{ justifyContent: 'space-between', flexWrap: 'nowrap' }}>
                    <h2 className="h2" id="filter-title" style={{ margin: 0 }}>
                        Filtros
                    </h2>
                    <button className="iconbtn" type="button" aria-label="Fechar" onClick={close}>
                        <Icon name="close" size={16} />
                    </button>
                </div>
            </div>

            <div className="export-body">
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
            </div>

            <div className="export-foot">
                {fields.length > 0 && (
                    <button className="btn" type="button" onClick={() => setDraft({})}>
                        Limpar
                    </button>
                )}
                <button className="btn" type="button" onClick={close}>
                    Cancelar
                </button>
                {fields.length > 0 && (
                    <button className="btn btn-primary" type="button" onClick={apply}>
                        Aplicar
                    </button>
                )}
            </div>
        </dialog>
    )
}
