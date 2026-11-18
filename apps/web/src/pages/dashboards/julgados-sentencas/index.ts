import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { JulgadosSentencasContent } from './JulgadosSentencasContent.tsx'
import { julgadosSentencasExport } from './exportFields.ts'
import { sentencasFilters } from './filters.ts'
import type { JulgadosSentencasResponse } from './types.ts'

// O dashboard Julgados Sentenças (LexFlow, unidades NG, LA e RJ): as páginas julgados_sentenca_{NG,LA,RJ} da v1
// numa só. A API já junta as duas buscas da página da v1 (com e sem período): o "mês a mês" e as opções de
// matéria do histórico chegam na mesma resposta.
export const julgadosSentencas: DashboardModule<JulgadosSentencasResponse> = {
    key: 'julgados-sentencas',
    fetch: (query) => dataClient.getDashboardData<JulgadosSentencasResponse>('julgados-sentencas', query),
    Content: JulgadosSentencasContent,
    filters: (data, current) => sentencasFilters(data, current),
    exportFields: julgadosSentencasExport,
}
