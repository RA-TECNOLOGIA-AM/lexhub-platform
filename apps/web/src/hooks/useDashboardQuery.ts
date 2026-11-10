import { useSearchParams } from 'react-router'
import { paramsFromQuery, queryFromParams, type DashboardParams } from '../lib/dashboardQuery.ts'
import type { Period } from '../lib/period.ts'
import type { DashboardFilters } from '../types/index.ts'

// Módulo: o período e os filtros do dashboard aberto, guardados na URL.
// Devolve: query (o que vale agora), search (texto da URL, para refazer a busca) e quem muda cada parte.
// Esconde: o formato da URL (lib/dashboardQuery.ts) e o useSearchParams.
export function useDashboardQuery() {
    const [params, setParams] = useSearchParams()
    const query = queryFromParams(params)
    const update = (next: Partial<DashboardParams>) => setParams(paramsFromQuery({ ...query, ...next }))

    return {
        query,
        search: params.toString(),
        setPeriod: (period: Period) => update(period),
        setFilters: (filters: DashboardFilters) => update({ filters }),
    }
}
