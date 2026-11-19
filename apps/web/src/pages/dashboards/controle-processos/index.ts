import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { ControleContent } from './ControleContent.tsx'
import { filtrosControle, type ControleResponse } from './controle.ts'

// Controle de Processos (NG, área Jurídico): a página da v1, com as 10 chamadas dela numa resposta só (LexFlow,
// banco NG legado e LexPre). Sem exportação e sem comissão, como a v1.
export const controleProcessos: DashboardModule<ControleResponse> = {
    key: 'controle-processos',
    fetch: (query) => dataClient.getDashboardData<ControleResponse>('controle-processos', query),
    Content: ControleContent,
    filters: filtrosControle,
}
