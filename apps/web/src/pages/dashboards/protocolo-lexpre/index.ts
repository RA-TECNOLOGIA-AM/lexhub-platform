import { dataClient } from '../../../services/client.ts'
import type { ProtocoloResponse } from '../../../types/index.ts'
import type { DashboardModule } from '../types.ts'
import { ProtocoloContent } from './ProtocoloContent.tsx'
import { protocoloFilters } from './filters.ts'
import { protocoloExport } from './exportFields.ts'

// O dashboard Protocolo (LexPre): de onde vêm os dados e como mostrar.
export const protocoloLexpre: DashboardModule<ProtocoloResponse> = {
    key: 'protocolo-lexpre',
    fetch: (query) => dataClient.getProtocolo(query),
    Content: ProtocoloContent,
    filters: (data) => protocoloFilters(data.opcoes_filtro),
    exportFields: protocoloExport,
}
