import type { Meta } from '../../../types/index.ts'

// Resposta de GET /orgs/{org}/geral/dashboards/estrategico-geral (app/routes/org_dashboards.py).
// Esqueleto: uma entrada por unidade que o dashboard reúne; as análises entram em `data`.
export type EstrategicoGeralUnit = {
    code: string // 'NG' | 'LA' | 'RJ'
    name: string
    data: Record<string, unknown>
}

export type EstrategicoGeralResponse = {
    meta: Meta // unit = 'geral'
    units: EstrategicoGeralUnit[]
}
