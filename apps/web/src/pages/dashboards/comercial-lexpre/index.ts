import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { ComercialLexpreContent } from './ComercialLexpreContent.tsx'
import type { ComercialLexpreResponse } from './types.ts'

// O dashboard Comercial (LexPre): de onde vêm os dados e como mostrar.
export const comercialLexpre: DashboardModule<ComercialLexpreResponse> = {
    key: 'comercial-lexpre',
    fetch: (query) => dataClient.getDashboardData<ComercialLexpreResponse>('comercial-lexpre', query),
    Content: ComercialLexpreContent,
}
