import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { EstrategicoGeralContent } from './EstrategicoGeralContent.tsx'
import type { EstrategicoGeralResponse } from './types.ts'

// Estratégico Geral (Owner e Desenvolvedor): NG, LAAM e LARJ numa tela só, pela rota da organização
// (/:org/geral/dashboards/estrategico-geral). Por enquanto só o esqueleto: as análises entram depois.
export const estrategicoGeral: DashboardModule<EstrategicoGeralResponse> = {
    key: 'estrategico-geral',
    fetch: (query) => dataClient.getOrgDashboardData<EstrategicoGeralResponse>('estrategico-geral', query),
    Content: EstrategicoGeralContent,
}
