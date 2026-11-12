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

// Uma etiqueta de filtro em uso ("Matéria: ANP"): o que mostra e o que tirar ao clicar no ✕.
export type FilterChip = { key: keyof DashboardFilters; value: string; label: string }

// Os filtros em uso como etiquetas, na ordem dos campos do dashboard. Valor sem opção conhecida mostra o próprio valor.
export function filterChips(fields: FilterField[], filters: DashboardFilters): FilterChip[] {
    const known = new Set(fields.map((f) => f.key))
    const chips: FilterChip[] = []
    for (const field of fields) {
        for (const value of filters[field.key] ?? []) {
            const option = field.options.find((o) => o.value === value)
            chips.push({ key: field.key, value, label: `${field.label}: ${option?.label ?? value}` })
        }
    }
    // Filtro na URL que o dashboard não declarou (ex.: link antigo): aparece com o nome técnico.
    for (const [key, values] of Object.entries(filters) as [keyof DashboardFilters, string[] | undefined][]) {
        if (known.has(key)) continue
        for (const value of values ?? []) chips.push({ key, value, label: `${String(key)}: ${value}` })
    }
    return chips
}

// Marca ou desmarca um valor. Filtro que fica sem nenhum valor sai do objeto (não vai para a URL).
export function toggleFilter(filters: DashboardFilters, key: keyof DashboardFilters, value: string): DashboardFilters {
    const current = filters[key] ?? []
    const next = current.includes(value) ? current.filter((v) => v !== value) : [...current, value]
    const result: DashboardFilters = { ...filters, [key]: next }
    if (next.length === 0) delete result[key]
    return result
}
