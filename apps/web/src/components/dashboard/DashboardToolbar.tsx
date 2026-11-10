import type { ExportFormat, ExportGroup } from '../../lib/exportFields.ts'
import type { FilterField } from '../../lib/filters.ts'
import type { Period } from '../../lib/period.ts'
import type { DashboardFilters } from '../../types/index.ts'
import { ExportButton } from './ExportButton.tsx'
import { FilterPanel } from './FilterPanel.tsx'
import { PeriodPicker } from './PeriodPicker.tsx'

type DashboardToolbarProps = {
    period: Period | null
    onPeriodChange: (period: Period) => void
    filterFields: FilterField[]
    filters: DashboardFilters
    onFiltersChange: (filters: DashboardFilters) => void
    exportTitle: string
    exportGroups: ExportGroup[]
    canExport: boolean
    onExport: (format: ExportFormat, campos: string[]) => Promise<void>
}

// Módulo: a barra de ações de todo dashboard (Período · Filtros · Exportar). Só junta as peças.
export function DashboardToolbar({
    period,
    onPeriodChange,
    filterFields,
    filters,
    onFiltersChange,
    exportTitle,
    exportGroups,
    canExport,
    onExport,
}: DashboardToolbarProps) {
    return (
        <>
            <PeriodPicker value={period} onChange={onPeriodChange} />
            <FilterPanel fields={filterFields} value={filters} onChange={onFiltersChange} />
            <ExportButton canExport={canExport} title={exportTitle} groups={exportGroups} onExport={onExport} />
        </>
    )
}
