import type { Period } from '../../lib/period.ts'
import { PeriodPicker } from './PeriodPicker.tsx'

type DashboardToolbarProps = {
    period: Period | null
    onPeriodChange: (period: Period) => void
}

// Módulo: a barra de ações de todo dashboard (Período · Filtros · Exportar). Filtros e Exportar entram nos passos 5 e 6.
export function DashboardToolbar({ period, onPeriodChange }: DashboardToolbarProps) {
    return <PeriodPicker value={period} onChange={onPeriodChange} />
}
