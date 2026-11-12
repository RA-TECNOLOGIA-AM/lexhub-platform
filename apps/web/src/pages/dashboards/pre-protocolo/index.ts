import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { PreProtocoloContent } from './PreProtocoloContent.tsx'
import type { PreProtocoloResponse } from './setores.ts'

// O dashboard Pré-protocolo (LexPre, unidades NG, LA e RJ): de onde vêm os dados e como mostrar.
export const preProtocolo: DashboardModule<PreProtocoloResponse> = {
    key: 'pre-protocolo',
    fetch: (query) => dataClient.getDashboardData<PreProtocoloResponse>('pre-protocolo', query),
    Content: PreProtocoloContent,
}
