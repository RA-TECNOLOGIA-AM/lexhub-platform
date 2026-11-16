import { COL_COMISSAO, COL_FUNCIONARIO } from '../../../lib/commissionReport.ts'
import { fmt } from '../../../lib/format.ts'
import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { OrgDocumentosLegadoContent } from './OrgDocumentosLegadoContent.tsx'
import { orgDocumentosLegadoFilters } from './filters.ts'
import { lerOrgDocumentos } from './orgDocumentos.ts'

// O dashboard Organização de documentos (banco legado: NG e RJ no banco NG), com os gráficos da v1.
export const orgDocumentos: DashboardModule<V1GenericoResponse> = {
    key: 'org-documentos',
    fetch: (query) => dataClient.getDashboardData<V1GenericoResponse>('org-documentos', query),
    Content: OrgDocumentosLegadoContent,
    filters: (data) => orgDocumentosLegadoFilters(lerOrgDocumentos(data)),
    // Mesmas colunas do PDF da v1: valor de causa, quantidade de resolvidos e comissão.
    commission: (data) => ({
        columns: [
            COL_FUNCIONARIO,
            { key: 'valor_causa_gerado', label: 'Valor de causa', format: fmt.brl, sum: true },
            { key: 'qtd_resolvidos', label: 'Qtd resolvidos', format: fmt.int, sum: true },
            COL_COMISSAO,
        ],
        rows: lerOrgDocumentos(data).comissao,
        sortBy: 'valor_comissao',
    }),
}
