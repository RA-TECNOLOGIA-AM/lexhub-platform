import { useRef, useState, type ReactNode } from 'react'
import { countFilters, filterChips, semInline, soInline, toggleFilter, type FilterField } from '../../lib/filters.ts'
import type { DashboardFilters } from '../../types/index.ts'
import { TopbarPortal } from '../layout/TopbarSlot.tsx'
import { Icon } from '../ui/Icon.tsx'
import { FilterDialog } from './FilterDialog.tsx'

type DashboardToolbarProps = {
    filterFields: FilterField[]
    filters: DashboardFilters
    onFiltersChange: (filters: DashboardFilters) => void
    period: ReactNode // o Período (vai na topbar, logo depois de Filtros)
}

// Módulo: os controles de todo dashboard.
// Na topbar: "Filtros" (abre a janela; azul com o número quando há filtro) e o Período.
// Na faixa logo abaixo (só com filtro em uso): "Filtros ativos" (✕ tira um) e "Limpar todos".
// Exportar, Gerar comissão e Atualizar ficam no cabeçalho (DashboardHeader).
export function DashboardToolbar({ filterFields, filters, onFiltersChange, period }: DashboardToolbarProps) {
    const [filtersOpen, setFiltersOpen] = useState(false)
    const filterButton = useRef<HTMLButtonElement>(null)
    const chips = filterChips(filterFields, filters)
    // Seletores de seção (`inline`) ficam fora do contador, da janela e do "Limpar todos".
    const count = countFilters(semInline(filters, filterFields))
    const dialogFields = filterFields.filter((f) => !f.inline)
    const limparTodos = () => onFiltersChange(soInline(filters, filterFields))

    function closeFilters() {
        setFiltersOpen(false)
        filterButton.current?.focus()
    }

    return (
        <>
            {/* Só existem enquanto o dashboard está na tela. */}
            <TopbarPortal>
                <button
                    ref={filterButton}
                    className={count > 0 ? 'btn btn-info' : 'btn'}
                    type="button"
                    aria-haspopup="dialog"
                    onClick={() => setFiltersOpen(true)}
                >
                    <Icon name="filter" size={16} />
                    Filtros
                    {count > 0 && (
                        <span className="count-badge" aria-label={`${count} em uso`}>
                            {count}
                        </span>
                    )}
                </button>
                {period}
            </TopbarPortal>

            {/* A faixa só aparece com filtro em uso. */}
            {chips.length > 0 && (
                <div className="dash-bar" role="toolbar" aria-label="Filtros ativos">
                    <div className="dash-bar-chips">
                        <span className="dash-bar-label">
                            <Icon name="sliders" size={15} />
                            Filtros ativos:
                        </span>
                        {chips.map((chip) => (
                            <span key={`${chip.key}:${chip.value}`} className="chip" title={chip.label}>
                                {chip.text}
                                <button
                                    type="button"
                                    aria-label={`Tirar o filtro ${chip.label}`}
                                    onClick={() => onFiltersChange(toggleFilter(filters, chip.key, chip.value))}
                                >
                                    <Icon name="close" size={12} />
                                </button>
                            </span>
                        ))}
                    </div>
                    <div className="dash-bar-actions">
                        <button type="button" className="linkbtn muted" onClick={limparTodos}>
                            Limpar todos
                        </button>
                    </div>
                </div>
            )}

            {filtersOpen && (
                <FilterDialog
                    fields={dialogFields}
                    value={filters}
                    onApply={(next) =>
                        onFiltersChange({ ...soInline(filters, filterFields), ...semInline(next, filterFields) })
                    }
                    onClose={closeFilters}
                />
            )}
        </>
    )
}
