import type { DashboardFilters } from '../types/index.ts'

// Módulo: os filtros dos dashboards, sem React (testado em filters.test.ts).

// Um filtro que o dashboard oferece: qual parâmetro (key), o nome na tela e as opções.
export type FilterField = {
    key: keyof DashboardFilters
    label: string
    options: { value: string; label: string }[]
    single?: boolean // um valor só (a API só usa o primeiro): escolher outro troca, não soma
    // Seletor que fica dentro de uma seção ou modal (ex.: os anos da Conversão no Financeiro Estratégico): vai
    // na URL e na API como os outros, mas não aparece na janela Filtros, nas etiquetas nem no "Limpar todos".
    inline?: boolean
}

// Só os filtros da página (sem os seletores de seção, `inline`): os da janela, das etiquetas e do contador.
export function semInline(filters: DashboardFilters, fields: FilterField[]): DashboardFilters {
    const inline = new Set(fields.filter((f) => f.inline).map((f) => f.key))
    return Object.fromEntries(Object.entries(filters).filter(([k]) => !inline.has(k as keyof DashboardFilters)))
}

// Só os seletores de seção (`inline`): o que "Limpar todos" mantém.
export function soInline(filters: DashboardFilters, fields: FilterField[]): DashboardFilters {
    const inline = new Set(fields.filter((f) => f.inline).map((f) => f.key))
    return Object.fromEntries(Object.entries(filters).filter(([k]) => inline.has(k as keyof DashboardFilters)))
}

// Quantos valores estão escolhidos no total: o "(2)" do botão Filtros.
export const countFilters = (filters: DashboardFilters): number =>
    Object.values(filters).reduce((total, values) => total + (values?.length ?? 0), 0)

// Uma etiqueta de filtro em uso: text = só o valor ("ANP"), label = com o nome do filtro ("Matéria: ANP",
// para o leitor de tela e a dica) e o que tirar ao clicar no ✕.
export type FilterChip = { key: keyof DashboardFilters; value: string; label: string; text: string }

// Os filtros em uso como etiquetas, na ordem dos campos do dashboard. Valor sem opção conhecida mostra o próprio valor.
export function filterChips(fields: FilterField[], filters: DashboardFilters): FilterChip[] {
    const known = new Set(fields.map((f) => f.key))
    const chips: FilterChip[] = []
    for (const field of fields) {
        if (field.inline) continue // seletor de seção: aparece na própria seção
        for (const value of filters[field.key] ?? []) {
            const option = field.options.find((o) => o.value === value)
            const text = option?.label ?? value
            chips.push({ key: field.key, value, label: `${field.label}: ${text}`, text })
        }
    }
    // Filtro na URL que o dashboard não declarou (ex.: link antigo): aparece com o nome técnico.
    for (const [key, values] of Object.entries(filters) as [keyof DashboardFilters, string[] | undefined][]) {
        if (known.has(key)) continue
        for (const value of values ?? []) chips.push({ key, value, label: `${String(key)}: ${value}`, text: value })
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

// O texto do botão de um filtro na janela: o nome (nada escolhido), a opção (uma) ou "ANP +2" (várias).
export function pickerLabel(field: FilterField, chosen: string[]): string {
    if (chosen.length === 0) return field.label
    const first = field.options.find((o) => o.value === chosen[0])?.label ?? chosen[0]
    return chosen.length === 1 ? first : `${first} +${chosen.length - 1}`
}

// Tira um filtro inteiro (todas as opções dele).
export function clearFilter(filters: DashboardFilters, key: keyof DashboardFilters): DashboardFilters {
    const result = { ...filters }
    delete result[key]
    return result
}

// Marca um valor num filtro de escolha única: o mesmo valor desmarca; outro troca.
export function pickSingle(filters: DashboardFilters, key: keyof DashboardFilters, value: string): DashboardFilters {
    return filters[key]?.includes(value) ? clearFilter(filters, key) : { ...filters, [key]: [value] }
}
