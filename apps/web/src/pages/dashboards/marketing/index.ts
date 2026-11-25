import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { MarketingNgContent } from './MarketingNgContent.tsx'
import { marketingNgFilters, type MarketingNgResponse } from './marketingNg.ts'

// O dashboard Marketing (banco NG, só a unidade NG; v1: /marketing_NG): de onde vêm os dados e como mostrar.
export const marketing: DashboardModule<MarketingNgResponse> = {
    key: 'marketing',
    fetch: (query) => dataClient.getDashboardData<MarketingNgResponse>('marketing', query),
    Content: MarketingNgContent,
    filters: marketingNgFilters,
}
