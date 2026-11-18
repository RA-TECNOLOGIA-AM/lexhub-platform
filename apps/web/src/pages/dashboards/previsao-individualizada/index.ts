import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { PrevisaoContent } from './PrevisaoContent.tsx'
import type { PrevisaoResponse } from './previsao.ts'

// Previsão Individualizada (TCC, Fase 6, área Estratégico): o bundle estático do XGBoost-AFT, só do escritório da
// unidade; o formulário e todo o cálculo ficam na própria página.
export const previsaoIndividualizada: DashboardModule<PrevisaoResponse> = {
    key: 'previsao-individualizada',
    fetch: (query) => dataClient.getDashboardData<PrevisaoResponse>('previsao-individualizada', query),
    Content: PrevisaoContent,
}
