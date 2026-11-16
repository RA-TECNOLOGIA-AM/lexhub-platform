import { COL_FUNCIONARIO } from '../../../lib/commissionReport.ts'
import { fmt } from '../../../lib/format.ts'
import { dataClient } from '../../../services/client.ts'
import type { PendenciasResponse } from '../../../types/index.ts'
import type { DashboardModule } from '../types.ts'
import { PendenciasContent } from './PendenciasContent.tsx'
import { pendenciasExport } from './exportFields.ts'
import { pendenciasFilters } from './filters.ts'

// O dashboard Pendências (LexPre): de onde vêm os dados e como mostrar.
export const pendenciasLexpre: DashboardModule<PendenciasResponse> = {
    key: 'pendencias-lexpre',
    fetch: (query) => dataClient.getPendencias(query),
    Content: PendenciasContent,
    filters: (data) => pendenciasFilters(data.opcoes_filtro),
    exportFields: pendenciasExport,
    // Mesmas colunas da v1: taxas (definem o valor por resolvida), quantidade, R$ por resolvida e comissão.
    commission: (data) => ({
        columns: [
            COL_FUNCIONARIO,
            { key: 'taxa_resolvido', label: 'Taxa resolvido', format: fmt.pct },
            { key: 'taxa_cancelamento', label: 'Taxa cancelamento', format: fmt.pct },
            { key: 'qtd_resolvido', label: 'Resolvidas', format: fmt.int, sum: true },
            { key: 'valor', label: 'R$/resolvida', format: fmt.brl },
            { key: 'comissao', label: 'Comissão', format: fmt.brl, sum: true },
        ],
        rows: data.comissionamento_pendencias_por_funcionario ?? [],
        sortBy: 'comissao',
    }),
}
