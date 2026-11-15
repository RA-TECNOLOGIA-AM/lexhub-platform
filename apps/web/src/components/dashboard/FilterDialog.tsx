import { useEffect, useId, useLayoutEffect, useRef, useState, type CSSProperties } from 'react'
import { Modal } from '../ui/Modal.tsx'
import { Icon, type IconName } from '../ui/Icon.tsx'
import { clearFilter, pickerLabel, toggleFilter, type FilterField } from '../../lib/filters.ts'
import type { DashboardFilters } from '../../types/index.ts'

type FilterDialogProps = {
    fields: FilterField[] // os filtros que o dashboard oferece ([] = nenhum)
    value: DashboardFilters // os filtros em uso (vêm da URL)
    onApply: (filters: DashboardFilters) => void
    onClose: () => void
}

// Ícone de cada filtro (o mesmo da v1); filtro novo sem ícone fica com o funil.
const ICONS: Partial<Record<keyof DashboardFilters, IconName>> = {
    funcionario: 'sliders',
    area_atuacao_id: 'briefcase',
    uf: 'pin',
    materia: 'book',
}

// Módulo: a janela "Filtros", como na v1: um botão por filtro (mostra o que está escolhido) que abre um menu
// logo abaixo dele, com busca, as opções e "Limpar seleção". Cada marcação já vale (a URL muda e os dados
// recarregam atrás da janela); "Limpar todos" tira tudo e "Fechar" só fecha. Usa o Modal da casa.
export function FilterDialog({ fields, value, onApply, onClose }: FilterDialogProps) {
    const [filters, setFilters] = useState<DashboardFilters>(value)
    const [open, setOpen] = useState<keyof DashboardFilters | null>(null)

    function change(next: DashboardFilters) {
        setFilters(next)
        onApply(next)
    }
    const anySelected = fields.some((f) => (filters[f.key]?.length ?? 0) > 0)

    return (
        <Modal
            title="Filtros"
            className="filter-dialog"
            onClose={onClose}
            footer={
                <>
                    {fields.length > 0 && (
                        <button
                            className="btn btn-ghost"
                            type="button"
                            disabled={!anySelected}
                            onClick={() => change({})}
                        >
                            Limpar todos
                        </button>
                    )}
                    <button className="btn btn-info" type="button" onClick={onClose}>
                        Fechar
                    </button>
                </>
            }
        >
            {fields.length === 0 ? (
                <p className="muted small" style={{ margin: 0 }}>
                    Este dashboard ainda não tem filtros.
                </p>
            ) : (
                <div className="fpicks">
                    {fields.map((field) => (
                        <FilterPicker
                            key={field.key}
                            field={field}
                            chosen={filters[field.key] ?? []}
                            open={open === field.key}
                            onOpenChange={(isOpen) => setOpen(isOpen ? field.key : null)}
                            onToggle={(v) => change(toggleFilter(filters, field.key, v))}
                            onClear={() => change(clearFilter(filters, field.key))}
                        />
                    ))}
                </div>
            )}
        </Modal>
    )
}

type FilterPickerProps = {
    field: FilterField
    chosen: string[]
    open: boolean
    onOpenChange: (open: boolean) => void
    onToggle: (value: string) => void
    onClear: () => void
}

const MENU_W = 240

// Um filtro: o botão e, aberto, o menu flutuante. O menu usa position: fixed (calculada a partir do botão)
// para passar por cima da borda da janela, como na v1. Fecha com Esc (só o menu, não a janela) ou clique fora.
function FilterPicker({ field, chosen, open, onOpenChange, onToggle, onClear }: FilterPickerProps) {
    const button = useRef<HTMLButtonElement>(null)
    const menu = useRef<HTMLDivElement>(null)
    const [query, setQuery] = useState('')
    const [pos, setPos] = useState<CSSProperties>({})
    const menuId = useId()

    // Posição: embaixo do botão, alinhado à direita dele (sem sair da tela). Recalcula ao rolar/redimensionar.
    useLayoutEffect(() => {
        if (!open) return
        const place = () => {
            const r = button.current?.getBoundingClientRect()
            if (!r) return
            const width = Math.min(MENU_W, window.innerWidth - 16)
            const left = Math.max(8, Math.min(r.right - width, window.innerWidth - width - 8))
            setPos({ top: r.bottom + 6, left, width })
        }
        place()
        window.addEventListener('resize', place)
        window.addEventListener('scroll', place, true)
        return () => {
            window.removeEventListener('resize', place)
            window.removeEventListener('scroll', place, true)
        }
    }, [open])

    // Clique fora do botão e do menu fecha.
    useEffect(() => {
        if (!open) return
        const onDown = (e: MouseEvent) => {
            const t = e.target as Node
            if (!menu.current?.contains(t) && !button.current?.contains(t)) onOpenChange(false)
        }
        document.addEventListener('mousedown', onDown)
        return () => document.removeEventListener('mousedown', onDown)
    }, [open, onOpenChange])

    const shown = field.options.filter((o) => o.label.toLowerCase().includes(query.trim().toLowerCase()))

    return (
        <div className="fpick-wrap">
            <button
                ref={button}
                type="button"
                className={chosen.length ? 'fpick on' : 'fpick'}
                aria-expanded={open}
                aria-controls={menuId}
                title={field.label}
                onClick={() => {
                    setQuery('')
                    onOpenChange(!open)
                }}
            >
                <Icon name={ICONS[field.key] ?? 'filter'} size={16} />
                <span className="fpick-text">{pickerLabel(field, chosen)}</span>
                <Icon name="chevron-down" size={14} />
            </button>
            {open && (
                <div
                    ref={menu}
                    id={menuId}
                    className="fmenu"
                    style={pos}
                    role="group"
                    aria-label={field.label}
                    onKeyDown={(e) => {
                        // Esc fecha só o menu: o preventDefault impede o <dialog> de fechar junto.
                        if (e.key !== 'Escape') return
                        e.preventDefault()
                        e.stopPropagation()
                        onOpenChange(false)
                        button.current?.focus()
                    }}
                >
                    <label className="fmenu-search">
                        <Icon name="search" size={16} />
                        <span className="sr-only">Buscar em {field.label}</span>
                        <input
                            autoFocus
                            type="search"
                            placeholder={`Buscar ${field.label}...`}
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />
                    </label>
                    <div className="fmenu-list">
                        {shown.length === 0 ? (
                            <span className="fmenu-empty">Nenhuma opção.</span>
                        ) : (
                            shown.map((option) => {
                                const checked = chosen.includes(option.value)
                                return (
                                    <label key={option.value} className="fmenu-opt">
                                        <input
                                            className="sr-only"
                                            type="checkbox"
                                            checked={checked}
                                            onChange={() => onToggle(option.value)}
                                        />
                                        <span className={checked ? 'fcheck on' : 'fcheck'} aria-hidden="true">
                                            {checked && <Icon name="check" size={12} />}
                                        </span>
                                        {option.label}
                                    </label>
                                )
                            })
                        )}
                    </div>
                    <div className="fmenu-foot">
                        <button type="button" className="btn btn-info" disabled={!chosen.length} onClick={onClear}>
                            Limpar seleção
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
