import type { DashboardFilters, Meta } from '../../../types/index.ts'
import type { FilterField } from '../../../lib/filters.ts'
import { DIMENSOES, filtrosDeClique, leitor, type Dimensao } from '../marketing/marketingComum.ts'

// Resposta do Marketing (LexPre) (API: app/dashboards/marketing_lexpre.py): a DashboardResponse da v1
// (/marketing_lexpre_NG e _LA) + `meta`. Os gráficos vêm em `charts`. As chaves levam o prefixo
// `marketing_lexpre_ng_` nas duas unidades (NG e LA), como na v1. No mock pode faltar qualquer campo: vira 0 / [].
export type MarketingLexpreResponse = {
    meta: Meta
    dashboard?: string // 'marketing_lexpre_NG' | 'marketing_lexpre_LA'
    stats?: Record<string, unknown>
    charts?: Record<string, unknown>
}

export const PREFIXO = 'marketing_lexpre_ng_'

// As dimensões do LexPre: todas, menos o dispositivo (não existe em perfil_clientes_lexpre).
export const DIMENSOES_LEXPRE = (Object.keys(DIMENSOES) as Dimensao[]).filter((d) => d !== 'dispositivo_marketing')

export const lerMarketing = (data: MarketingLexpreResponse) => leitor(data.stats, data.charts ?? {}, PREFIXO)

export const marketingFilters = (data: MarketingLexpreResponse, current: DashboardFilters = {}): FilterField[] =>
    filtrosDeClique(lerMarketing(data), DIMENSOES_LEXPRE, current)
