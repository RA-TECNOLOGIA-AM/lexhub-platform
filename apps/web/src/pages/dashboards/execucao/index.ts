import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { ExecucaoContent } from './ExecucaoContent.tsx'
import type { ExecucaoResponse } from './types.ts'

// O dashboard Execução (LexFlow): de onde vêm os dados e como mostrar.
export const execucao: DashboardModule<ExecucaoResponse> = {
    key: 'execucao',
    fetch: (query) => dataClient.getDashboardData<ExecucaoResponse>('execucao', query),
    Content: ExecucaoContent,
}
