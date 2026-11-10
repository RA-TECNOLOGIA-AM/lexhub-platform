import { useRef, useState } from 'react'
import { Icon } from '../ui/Icon.tsx'
import { useDismiss } from '../../hooks/useDismiss.ts'
import { countFilters, toggleFilter, type FilterField } from '../../lib/filters.ts'
import type { DashboardFilters } from '../../types/index.ts'

type FilterPanelProps = {
    fields: FilterField[] // os filtros que o dashboard oferece ([] = nenhum)
    value: DashboardFilters // os filtros em uso (vêm da URL)
    onChange: (filters: DashboardFilters) => void
}

// Módulo: o botão "Filtros (2)" e o painel com uma lista de opções por filtro.
// Como o período, edita um rascunho e só muda a URL no Aplicar.
export function FilterPanel({ fields, value, onChange }: FilterPanelProps) {
    const [open, setOpen] = useState(false)
    const [draft, setDraft] = useState<DashboardFilters>(value)
    const root = useRef<HTMLDivElement>(null)
    const button = useRef<HTMLButtonElement>(null)

    useDismiss({
        open,
        onClose: () => setOpen(false),
        isInside: (target) => !!root.current?.contains(target),
        returnFocus: button,
    })

    const count = countFilters(value)

    function toggle() {
        if (!open) setDraft(value)
        setOpen((o) => !o)
    }

    function apply() {
        onChange(draft)
        setOpen(false)
        button.current?.focus()
    }

    return (
        <div className="popover-wrap" ref={root}>
            <button
                ref={button}
                className="btn"
                type="button"
                aria-expanded={open}
                aria-haspopup="dialog"
                onClick={toggle}
            >
                <Icon name="filter" size={16} />
                {count > 0 ? `Filtros (${count})` : 'Filtros'}
            </button>
            {open && (
                <div className="card popover" role="dialog" aria-label="Filtros">
                    {fields.length === 0 ? (
                        <p className="muted small" style={{ margin: 0 }}>
                            Este dashboard ainda não tem filtros.
                        </p>
                    ) : (
                        <div className="filter-groups">
                            {fields.map((field) => (
                                <fieldset key={field.key} className="filter-group">
                                    <legend className="lbl">{field.label}</legend>
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
                                </fieldset>
                            ))}
                        </div>
                    )}
                    <div className="popover-actions">
                        {fields.length > 0 && (
                            <button className="btn" type="button" onClick={() => setDraft({})}>
                                Limpar
                            </button>
                        )}
                        <button className="btn btn-primary" type="button" onClick={fields.length > 0 ? apply : toggle}>
                            {fields.length > 0 ? 'Aplicar' : 'Fechar'}
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
