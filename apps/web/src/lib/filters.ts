import type { DashboardFilters } from '../types/index.ts'

// Módulo: os filtros dos dashboards, sem React (testado em filters.test.ts).

// Um filtro que o dashboard oferece: qual parâmetro (key), o nome na tela e as opções.
export type FilterField = {
    key: keyof DashboardFilters
    label: string
    options: { value: string; label: string }[]
}

// Quantos valores estão escolhidos no total: o "(2)" do botão Filtros.
export const countFilters = (filters: DashboardFilters): number =>
    Object.values(filters).reduce((total, values) => total + (values?.length ?? 0), 0)

// Marca ou desmarca um valor. Filtro que fica sem nenhum valor sai do objeto (não vai para a URL).
export function toggleFilter(filters: DashboardFilters, key: keyof DashboardFilters, value: string): DashboardFilters {
    const current = filters[key] ?? []
    const next = current.includes(value) ? current.filter((v) => v !== value) : [...current, value]
    const result: DashboardFilters = { ...filters, [key]: next }
    if (next.length === 0) delete result[key]
    return result
}
