import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { ComissaoLexpreContent } from './ComissaoLexpreContent.tsx'
import type { ComissaoLexpreResponse } from './types.ts'

// O dashboard Comissão Comercial (LexPre): de onde vêm os dados e como mostrar.
export const comissaoLexpre: DashboardModule<ComissaoLexpreResponse> = {
    key: 'comissao-lexpre',
    fetch: (query) => dataClient.getDashboardData<ComissaoLexpreResponse>('comissao-lexpre', query),
    Content: ComissaoLexpreContent,
}
