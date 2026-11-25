import type { FilterField } from '../../../lib/filters.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { DIMENSOES, filtrosDeClique, leitor, type Dimensao } from './marketingComum.ts'

// Resposta do Marketing (banco NG): a DashboardResponse da v1 (/marketing_NG) + `meta`. Como na v1, os números
// vêm em `stats` e os gráficos soltos na resposta (marketing_ng_faixa_etaria, ...). No mock pode faltar tudo.
export type MarketingNgResponse = V1GenericoResponse &
    Record<string, unknown> & {
        // Novo na V2: o comercial do LexPre (escritório da NG) somado aos números do banco NG (o comercial foi para o
        // LexPre em set/2026). somado = false: só o banco NG, e o motivo.
        lexpre?: { somado: boolean; motivo: string | null }
    }

export const PREFIXO_NG = 'marketing_ng_'

export const lerMarketingNg = (data: MarketingNgResponse) => leitor(data.stats, data, PREFIXO_NG)

export const marketingNgFilters = (data: MarketingNgResponse, current: DashboardFilters = {}): FilterField[] =>
    filtrosDeClique(lerMarketingNg(data), Object.keys(DIMENSOES) as Dimensao[], current)
