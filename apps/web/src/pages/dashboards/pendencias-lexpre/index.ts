import { dataClient } from '../../../services/client.ts'
import type { PendenciasResponse } from '../../../types/index.ts'
import type { DashboardModule } from '../types.ts'
import { PendenciasContent } from './PendenciasContent.tsx'
import { pendenciasExport } from './exportFields.ts'

// O dashboard Pendências (LexPre): de onde vêm os dados e como mostrar.
export const pendenciasLexpre: DashboardModule<PendenciasResponse> = {
    key: 'pendencias-lexpre',
    fetch: (query) => dataClient.getPendencias(query),
    Content: PendenciasContent,
    exportFields: pendenciasExport,
}
