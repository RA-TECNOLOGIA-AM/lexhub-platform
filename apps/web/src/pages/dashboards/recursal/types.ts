import type { Meta } from '../../../types/index.ts'

// Resposta de GET /orgs/{org}/units/{unit}/dashboards/recursal: a DashboardResponse genérica da v1 + meta.
// Os nomes dos campos levam o sufixo da unidade (ex.: total_recursal_NG, total_recursal_LA);
// quem escolhe o nome certo é o mapa em fields.ts. No mock vem só `meta` e `stats: {}`.
export type RecursalStats = Record<string, number | null | undefined>

export type RecursalResponse = {
    meta: Meta
    dashboard?: string // 'recursal_NG' ou 'recursal_LA' na v1
    stats?: RecursalStats
}
