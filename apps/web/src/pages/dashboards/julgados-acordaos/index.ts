import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { JulgadosAcordaosContent } from './JulgadosAcordaosContent.tsx'
import { julgadosAcordaosExport } from './exportFields.ts'
import { julgadosFilters } from './filters.ts'
import type { JulgadosAcordaosResponse } from './types.ts'

// O dashboard Julgados Acórdãos (LexFlow, unidades NG, LA e RJ): as páginas julgados_acordao_{NG,LA,RJ} da v1
// numa só. A API já junta as duas buscas da página da v1 (com e sem período): o "mês a mês" e as opções de
// matéria do histórico chegam na mesma resposta.
export const julgadosAcordaos: DashboardModule<JulgadosAcordaosResponse> = {
    key: 'julgados-acordaos',
    fetch: (query) => dataClient.getDashboardData<JulgadosAcordaosResponse>('julgados-acordaos', query),
    Content: JulgadosAcordaosContent,
    filters: (data, current) => julgadosFilters(data, current),
    exportFields: julgadosAcordaosExport,
}
