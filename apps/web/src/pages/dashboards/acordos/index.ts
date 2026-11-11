import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { AcordosContent } from './AcordosContent.tsx'
import type { AcordosResponse } from './types.ts'

// O dashboard Acordos (LexFlow; na v1, "Execução de Acordos"): de onde vêm os dados e como mostrar.
export const acordos: DashboardModule<AcordosResponse> = {
    key: 'acordos',
    fetch: (query) => dataClient.getDashboardData<AcordosResponse>('acordos', query),
    Content: AcordosContent,
}
