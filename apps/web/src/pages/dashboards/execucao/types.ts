import type { Meta } from '../../../types/index.ts'

// Resposta de GET /orgs/{org}/units/{unit}/dashboards/execucao: a DashboardResponse genérica da v1 + `meta`.
// Só tipamos o que a tela usa. Os nomes dos campos de `stats` mudam por unidade (ver fields.ts),
// por isso ficam como mapa solto; no mock vem `stats: {}`.
export type ExecucaoResponse = {
    meta: Meta
    dashboard?: string
    stats?: Record<string, unknown>
}
