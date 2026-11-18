import type { DashboardCatalog, DashboardSummary } from '../types/index.ts'

// Módulo: dashboard ligado/desligado por unidade (só o Desenvolvedor liga e desliga; a API confere).
// O catálogo manda as unidades desligadas em `disabled_units` só para quem pode religar.

// Desligado nesta unidade? Sem unidade (todas): desligado em todas as do card.
export function isDisabled(dashboard: DashboardSummary, unit: string | null): boolean {
    const off = dashboard.disabled_units ?? []
    if (unit) return off.includes(unit)
    return off.length > 0 && dashboard.units.every((u) => off.includes(u))
}

// O catálogo depois de ligar/desligar um dashboard numa unidade (o card guardado muda sem buscar de novo).
export function withEnabled(catalog: DashboardCatalog, key: string, unit: string, enabled: boolean): DashboardCatalog {
    return {
        ...catalog,
        available: catalog.available.map((d) => {
            if (d.key !== key) return d
            const others = (d.disabled_units ?? []).filter((u) => u !== unit)
            return { ...d, disabled_units: enabled ? others : [...others, unit] }
        }),
    }
}
