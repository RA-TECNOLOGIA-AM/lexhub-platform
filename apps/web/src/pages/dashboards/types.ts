import type { ComponentType } from 'react'
import type { DashboardQuery, Meta } from '../../types/index.ts'

// Contrato de um dashboard: tudo o que muda de um para outro, passado como parâmetro.
// T = formato da resposta; toda resposta de dashboard da V2 traz o bloco `meta`.
export type DashboardModule<T extends { meta: Meta }> = {
    key: string // o mesmo do catálogo e da API (ex.: 'protocolo-lexpre')
    fetch: (query: DashboardQuery) => Promise<T> // busca os dados de uma unidade
    Content: ComponentType<{ data: T }> // o miolo da página (KPIs, gráficos...)
}
