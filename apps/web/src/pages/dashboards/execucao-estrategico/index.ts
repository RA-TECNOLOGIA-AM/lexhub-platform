import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { EstrategicoContent } from './EstrategicoContent.tsx'
import { estrategicoExport, relatorioDoEscopo } from './exportFields.ts'
import { estrategicoFilters } from './filters.ts'
import type { EstrategicoResponse } from './estrategico.ts'

// O Execução Estratégico Geral (NG, LexFlow): Condenação e Acordos juntos, como a página da v1.
export const execucaoEstrategico: DashboardModule<EstrategicoResponse> = {
    key: 'execucao-estrategico',
    fetch: (query) => dataClient.getDashboardData<EstrategicoResponse>('execucao-estrategico', query),
    Content: EstrategicoContent,
    filters: estrategicoFilters,
    // O "Relatório" da v1: Condenação, Acordos ou os dois num arquivo só, com origem e recorte.
    exportReports: estrategicoExport,
    exportReportInicial: relatorioDoEscopo,
}
