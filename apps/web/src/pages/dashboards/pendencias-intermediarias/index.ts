import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { IntermediariasContent } from './IntermediariasContent.tsx'
import { intermediariasExport } from './exportFields.ts'
import {
    comissaoIntermediarias,
    filtrosIntermediarias,
    type PendenciasIntermediariasResponse,
} from './intermediarias.ts'

// Pendências Intermediárias (LexFlow, NG, LA e RJ, área Jurídico; o RJ com o cálculo do NG): a página da v1, com as duas chamadas dela (período
// e histórico) numa resposta só; comissão por taxa de dilação (as mesmas regras nas três unidades).
export const pendenciasIntermediarias: DashboardModule<PendenciasIntermediariasResponse> = {
    key: 'pendencias-intermediarias',
    fetch: (query) => dataClient.getDashboardData<PendenciasIntermediariasResponse>('pendencias-intermediarias', query),
    Content: IntermediariasContent,
    filters: filtrosIntermediarias,
    exportReports: intermediariasExport,
    commission: comissaoIntermediarias,
}
