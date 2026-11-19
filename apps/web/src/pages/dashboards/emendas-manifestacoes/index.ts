import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { EmendasContent } from './EmendasContent.tsx'
import { comissaoEmendas, filtrosEmendas, type EmendasResponse } from './emendas.ts'
import { emendasExport } from './exportFields.ts'

// Emendas e Manifestações (LexFlow, NG, LA e RJ, área Jurídico; o RJ com o cálculo do NG): a página da v1, com as duas chamadas dela (período e
// histórico) numa resposta só; comissão calculada pela API (NG: valor fixo por peça; LA: faixa pela agenda cumprida).
export const emendasManifestacoes: DashboardModule<EmendasResponse> = {
    key: 'emendas-manifestacoes',
    fetch: (query) => dataClient.getDashboardData<EmendasResponse>('emendas-manifestacoes', query),
    Content: EmendasContent,
    filters: filtrosEmendas,
    exportReports: emendasExport,
    commission: comissaoEmendas,
}
