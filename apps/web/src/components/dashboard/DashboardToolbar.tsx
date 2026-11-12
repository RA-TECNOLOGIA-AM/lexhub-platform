import { useRef, useState } from 'react'
import type { ExportFormat, ExportGroup } from '../../lib/exportFields.ts'
import { countFilters, filterChips, toggleFilter, type FilterField } from '../../lib/filters.ts'
import type { DashboardFilters } from '../../types/index.ts'
import { Icon } from '../ui/Icon.tsx'
import { ExportButton } from './ExportButton.tsx'
import { FilterDialog } from './FilterDialog.tsx'

type DashboardToolbarProps = {
    filterFields: FilterField[]
    filters: DashboardFilters
    onFiltersChange: (filters: DashboardFilters) => void
    exportTitle: string
    exportGroups: ExportGroup[]
    canExport: boolean
    onExport: (format: ExportFormat, campos: string[]) => Promise<void>
}

// Módulo: a faixa logo abaixo da topbar em todo dashboard. À esquerda, os filtros em uso (✕ tira um);
// à direita, "Filtros" (abre a janela) e "Exportar". O Período fica na topbar (DashboardView).
export function DashboardToolbar({
    filterFields,
    filters,
    onFiltersChange,
    exportTitle,
    exportGroups,
    canExport,
    onExport,
}: DashboardToolbarProps) {
    const [filtersOpen, setFiltersOpen] = useState(false)
    const filterButton = useRef<HTMLButtonElement>(null)
    const chips = filterChips(filterFields, filters)
    const count = countFilters(filters)

    function closeFilters() {
        setFiltersOpen(false)
        filterButton.current?.focus()
    }

    return (
        <div className="dash-bar" role="toolbar" aria-label="Filtros e exportação">
            <div className="dash-bar-chips">
                {chips.length === 0 ? (
                    <span className="muted small">Sem filtros: mostrando tudo do período.</span>
                ) : (
                    chips.map((chip) => (
                        <span key={`${chip.key}:${chip.value}`} className="chip">
                            {chip.label}
                            <button
                                type="button"
                                aria-label={`Tirar o filtro ${chip.label}`}
                                onClick={() => onFiltersChange(toggleFilter(filters, chip.key, chip.value))}
                            >
                                <Icon name="close" size={12} />
                            </button>
                        </span>
                    ))
                )}
            </div>
            <div className="dash-bar-actions">
                <button
                    ref={filterButton}
                    className="btn"
                    type="button"
                    aria-haspopup="dialog"
                    onClick={() => setFiltersOpen(true)}
                >
                    <Icon name="filter" size={16} />
                    {count > 0 ? `Filtros (${count})` : 'Filtros'}
                </button>
                <ExportButton canExport={canExport} title={exportTitle} groups={exportGroups} onExport={onExport} />
            </div>
            {filtersOpen && (
                <FilterDialog fields={filterFields} value={filters} onApply={onFiltersChange} onClose={closeFilters} />
            )}
        </div>
    )
}
