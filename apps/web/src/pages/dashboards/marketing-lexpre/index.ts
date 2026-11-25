import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { MarketingLexpreContent } from './MarketingLexpreContent.tsx'
import { marketingExport } from './exportFields.ts'
import { marketingFilters, type MarketingLexpreResponse } from './marketingLexpre.ts'

// O dashboard Marketing (LexPre) (v1: /marketing_lexpre_NG e _LA): de onde vêm os dados e como mostrar.
export const marketingLexpre: DashboardModule<MarketingLexpreResponse> = {
    key: 'marketing-lexpre',
    fetch: (query) => dataClient.getDashboardData<MarketingLexpreResponse>('marketing-lexpre', query),
    Content: MarketingLexpreContent,
    filters: marketingFilters,
    exportReports: marketingExport,
}
