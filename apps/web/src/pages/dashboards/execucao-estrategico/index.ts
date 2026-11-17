import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { EstrategicoContent } from './EstrategicoContent.tsx'
import { estrategicoFilters } from './filters.ts'
import type { EstrategicoResponse } from './estrategico.ts'

// O Execução Estratégico Geral (NG, LexFlow): Condenação e Acordos juntos, como a página da v1.
export const execucaoEstrategico: DashboardModule<EstrategicoResponse> = {
    key: 'execucao-estrategico',
    fetch: (query) => dataClient.getDashboardData<EstrategicoResponse>('execucao-estrategico', query),
    Content: EstrategicoContent,
    filters: estrategicoFilters,
}
