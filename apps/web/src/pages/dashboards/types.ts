import type { ComponentType } from 'react'
import type { DashboardFilters, DashboardQuery, Meta } from '../../types/index.ts'
import type { FilterField } from '../../lib/filters.ts'
import type { ExportGroup } from '../../lib/exportFields.ts'
import type { CommissionTable } from '../../lib/commissionReport.ts'

// Contrato de um dashboard: tudo o que muda de um para outro, passado como parâmetro.
// T = formato da resposta; toda resposta de dashboard da V2 traz o bloco `meta`.
export type DashboardModule<T extends { meta: Meta }> = {
    key: string // o mesmo do catálogo e da API (ex.: 'protocolo-lexpre')
    fetch: (query: DashboardQuery) => Promise<T> // busca os dados de uma unidade
    Content: ComponentType<ContentProps<T>> // o miolo da página (KPIs, gráficos...)
    filters?: (data: T) => FilterField[] // os filtros deste dashboard (opções vêm da resposta); sem = não tem filtros
    exportFields?: ExportGroup[] // campos do relatório (cópia da lista do servidor); sem = não exporta ainda
    // Tabela de comissão do período para o "Gerar comissão (PDF)"; sem = o botão não aparece. Vem da resposta,
    // e o botão só aparece para quem vê a comissão de todos (can_see_commission: Gestor/Desenvolvedor, como na v1).
    commission?: (data: T) => CommissionTable
}

// O que o miolo recebe: os dados e, para gráficos clicáveis, os filtros em uso e como marcar/desmarcar um.
export type ContentProps<T> = {
    data: T
    filters?: DashboardFilters
    onToggleFilter?: (key: keyof DashboardFilters, value: string) => void
}
