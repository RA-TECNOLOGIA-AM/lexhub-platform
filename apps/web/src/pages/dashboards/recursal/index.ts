import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { RecursalContent } from './RecursalContent.tsx'
import type { RecursalResponse } from './types.ts'

// O dashboard Recursal (LexFlow, unidades NG e LA): de onde vêm os dados e como mostrar.
export const recursal: DashboardModule<RecursalResponse> = {
    key: 'recursal',
    fetch: (query) => dataClient.getDashboardData<RecursalResponse>('recursal', query),
    Content: RecursalContent,
}
