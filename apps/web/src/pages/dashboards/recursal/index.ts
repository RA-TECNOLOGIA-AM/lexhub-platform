import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { RecursalContent } from './RecursalContent.tsx'
import { recursalExport } from './exportFields.ts'
import { recursalFilters } from './filters.ts'
import { comissaoRecursal, type RecursalResponse } from './recursal.ts'

// O Recursal (LexFlow, NG, LA e RJ): a página da v1, com as chamadas dela juntas numa resposta só.
export const recursal: DashboardModule<RecursalResponse> = {
    key: 'recursal',
    fetch: (query) => dataClient.getDashboardData<RecursalResponse>('recursal', query),
    Content: RecursalContent,
    filters: recursalFilters,
    exportFields: recursalExport,
    // Relatório de comissão do setor Recursos: só NG, como a v1 (no LA e no RJ o botão não aparece).
    commission: comissaoRecursal,
}
