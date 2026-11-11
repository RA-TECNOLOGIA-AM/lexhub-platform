import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { OrgDocumentosLexpreContent } from './OrgDocumentosLexpreContent.tsx'
import { orgDocumentosFilters } from './filters.ts'
import type { OrgDocumentosLexpreResponse } from './types.ts'

// O dashboard Organização de documentos (LexPre): de onde vêm os dados e como mostrar.
export const orgDocumentosLexpre: DashboardModule<OrgDocumentosLexpreResponse> = {
    key: 'org-documentos-lexpre',
    fetch: (query) => dataClient.getDashboardData<OrgDocumentosLexpreResponse>('org-documentos-lexpre', query),
    Content: OrgDocumentosLexpreContent,
    filters: (data) => orgDocumentosFilters(data.opcoes_filtro),
}
