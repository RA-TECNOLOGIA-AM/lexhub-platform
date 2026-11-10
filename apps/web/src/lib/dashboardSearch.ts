import type { DashboardSummary } from '../types/index.ts'
import { matchesText } from './text.ts'

// Nome da busca na URL (?busca=), o mesmo de Membros. O campo do topo escreve; o hub lê.
export const SEARCH_PARAM = 'busca'
// Módulo: a busca de dashboards (o campo "Buscar dashboard" do topo).
// A única coisa que ele decide: em quais campos procurar. Como comparar é com o lib/text.ts.
type Searchable = Pick<DashboardSummary, 'title' | 'area' | 'desc'>

// Campos que contam na busca: título, área e descrição. Campo novo = acrescentar aqui.
const searchText = (d: Searchable) => `${d.title} ${d.area} ${d.desc}`

export const searchDashboards = <T extends Searchable>(list: T[], query: string): T[] =>
    list.filter((d) => matchesText(searchText(d), query))
