import { COL_COMISSAO, COL_FUNCIONARIO } from '../../../lib/commissionReport.ts'
import { fmt } from '../../../lib/format.ts'
import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { OrgDocumentosLexpreContent } from './OrgDocumentosLexpreContent.tsx'
import { orgDocumentosExport } from './exportFields.ts'
import { orgDocumentosFilters } from './filters.ts'
import type { OrgDocumentosLexpreResponse } from './types.ts'

// O dashboard Organização de documentos (LexPre): de onde vêm os dados e como mostrar.
export const orgDocumentosLexpre: DashboardModule<OrgDocumentosLexpreResponse> = {
    key: 'org-documentos-lexpre',
    fetch: (query) => dataClient.getDashboardData<OrgDocumentosLexpreResponse>('org-documentos-lexpre', query),
    Content: OrgDocumentosLexpreContent,
    filters: (data) => orgDocumentosFilters(data.opcoes_filtro),
    exportFields: orgDocumentosExport,
    // Mesmas colunas da v1: protocolados (qtd e valor de causa) e comissão.
    commission: (data) => ({
        columns: [
            COL_FUNCIONARIO,
            { key: 'qtd_protocolados', label: 'Protocolados', format: fmt.int, sum: true },
            { key: 'valor_causa_protocolado', label: 'Valor protocolado', format: fmt.brl, sum: true },
            COL_COMISSAO,
        ],
        rows: data.comissionamento_por_funcionario ?? [],
        sortBy: 'valor_comissao',
    }),
}
