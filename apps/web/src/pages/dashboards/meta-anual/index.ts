import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { MetaAnualContent } from './MetaAnualContent.tsx'
import type { MetaAnualResponse } from './types.ts'

// O dashboard Meta anual (Financeiro; a planilha do financeiro de cada unidade no Google Sheets, NG e LA, com
// o mesmo cálculo e as metas de cada uma): de onde vêm os dados e como mostrar.
export const metaAnual: DashboardModule<MetaAnualResponse> = {
    key: 'meta-anual',
    fetch: (query) => dataClient.getDashboardData<MetaAnualResponse>('meta-anual', query),
    Content: MetaAnualContent,
}
