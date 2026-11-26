import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { EstrategicoContent } from './EstrategicoContent.tsx'
import type { EstrategicoResponse } from './estrategico.ts'
import { estrategicoFilters } from './filters.ts'

// Estratégico (área Estratégico): Comercial, Protocolo e Jurídico da unidade numa tela, como a página da v1
// (GERAL/Estrategico.tsx), cada unidade com os próprios números.
export const estrategico: DashboardModule<EstrategicoResponse> = {
    key: 'estrategico',
    fetch: (query) => dataClient.getDashboardData<EstrategicoResponse>('estrategico', query),
    Content: EstrategicoContent,
    filters: estrategicoFilters,
}
