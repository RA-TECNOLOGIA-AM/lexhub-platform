import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { ComercialLexpreContent } from './ComercialLexpreContent.tsx'
import { comercialExport } from './exportFields.ts'
import { comercialFilters } from './filters.ts'
import type { ComercialLexpreResponse } from './types.ts'

// O dashboard Comercial (LexPre): de onde vêm os dados e como mostrar.
export const comercialLexpre: DashboardModule<ComercialLexpreResponse> = {
    key: 'comercial-lexpre',
    fetch: (query) => dataClient.getDashboardData<ComercialLexpreResponse>('comercial-lexpre', query),
    Content: ComercialLexpreContent,
    filters: comercialFilters,
    // Sem "Gerar comissão" aqui (ela fica na Comissão Comercial); o relatório tem as colunas da query, como na v1.
    exportFields: comercialExport,
}
