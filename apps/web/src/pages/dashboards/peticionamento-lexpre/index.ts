import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { PeticionamentoLexpreContent } from './PeticionamentoLexpreContent.tsx'
import { peticionamentoFilters } from './filters.ts'
import type { PeticionamentoLexpreResponse } from './types.ts'

// O dashboard Peticionamento (LexPre): de onde vêm os dados e como mostrar.
export const peticionamentoLexpre: DashboardModule<PeticionamentoLexpreResponse> = {
    key: 'peticionamento-lexpre',
    fetch: (query) => dataClient.getDashboardData<PeticionamentoLexpreResponse>('peticionamento-lexpre', query),
    Content: PeticionamentoLexpreContent,
    filters: (data) => peticionamentoFilters(data.opcoes_filtro),
}
