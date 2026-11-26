import type { DashboardSummary } from '../types/index.ts'

// Módulo: dashboard da organização (scope 'org' no catálogo, ex.: Estratégico Geral). Junta as unidades em que
// está ligado numa tela só, e só Owner e Desenvolvedor o recebem (a regra é do banco). No lugar da unidade, a
// URL leva 'geral': /:org/geral/dashboards/:key (a mesma rota dos outros, então a casca é a mesma).
export const GERAL_UNIT = 'geral'

export const isOrgDashboard = (dashboard: Pick<DashboardSummary, 'scope'>): boolean => dashboard.scope === 'org'

// Para onde o card (ou um link) leva: o da organização ignora a unidade escolhida.
export function dashboardHref(org: string, unit: string, dashboard: Pick<DashboardSummary, 'key' | 'scope'>): string {
    return `/${org}/${isOrgDashboard(dashboard) ? GERAL_UNIT : unit}/dashboards/${dashboard.key}`
}

// O nome da "unidade" no cabeçalho: 'geral' vira 'Todas as unidades'; as outras ficam como vieram.
export const unitLabel = (unit: string, name: string): string => (unit === GERAL_UNIT ? 'Todas as unidades' : name)
