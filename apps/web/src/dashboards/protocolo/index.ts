import { dataClient } from '../../data/client.ts'
import type { ProtocoloResponse } from '../../data/types.ts'
import type { DashboardModule } from '../types.ts'
import { ProtocoloContent } from './ProtocoloContent.tsx'

// O dashboard Protocolo (LexPre): de onde vêm os dados e como mostrar.
export const protocolo: DashboardModule<ProtocoloResponse> = {
    key: 'protocolo-lexpre',
    fetch: (query) => dataClient.getProtocolo(query),
    Content: ProtocoloContent,
}
