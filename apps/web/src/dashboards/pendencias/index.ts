import { dataClient } from '../../data/client.ts'
import type { PendenciasResponse } from '../../data/types.ts'
import type { DashboardModule } from '../types.ts'
import { PendenciasContent } from './PendenciasContent.tsx'

// O dashboard Pendências (LexPre): de onde vêm os dados e como mostrar.
export const pendencias: DashboardModule<PendenciasResponse> = {
    key: 'pendencias',
    fetch: (query) => dataClient.getPendencias(query),
    Content: PendenciasContent,
}
