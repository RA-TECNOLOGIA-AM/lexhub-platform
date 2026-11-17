import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { AcordosContent } from './AcordosContent.tsx'
import { acordosFilters } from './filters.ts'

// O dashboard Acordos (LexFlow; na v1, "Execução de Acordos"): de onde vêm os dados e como mostrar. Os filtros
// estão em filters.ts.
export const acordos: DashboardModule<V1GenericoResponse> = {
    key: 'acordos',
    fetch: (query) => dataClient.getDashboardData<V1GenericoResponse>('acordos', query),
    Content: AcordosContent,
    filters: acordosFilters,
}
