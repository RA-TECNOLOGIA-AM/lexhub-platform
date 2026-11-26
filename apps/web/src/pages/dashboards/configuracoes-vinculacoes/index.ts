import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { VinculacoesContent } from './VinculacoesContent.tsx'
import { vinculacoesExport } from './exportFields.ts'
import { vinculacoesFilters } from './filters.ts'
import type { VinculacoesResponse } from './vinculacoes.ts'

// Configurações das Vinculações (LexFlow, área Estratégico): a auditoria das vinculações (setor + atividade) do
// escritório da unidade, como a página admin da v1. Os filtros valem na tela (no navegador) e na exportação.
export const configuracoesVinculacoes: DashboardModule<VinculacoesResponse> = {
    key: 'configuracoes-vinculacoes',
    fetch: (query) => dataClient.getDashboardData<VinculacoesResponse>('configuracoes-vinculacoes', query),
    Content: VinculacoesContent,
    filters: vinculacoesFilters,
    exportFields: vinculacoesExport,
}
