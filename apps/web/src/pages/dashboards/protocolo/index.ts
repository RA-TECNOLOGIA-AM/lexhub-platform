import { COL_COMISSAO, COL_FUNCIONARIO } from '../../../lib/commissionReport.ts'
import { fmt } from '../../../lib/format.ts'
import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { ProtocoloLegadoContent } from './ProtocoloLegadoContent.tsx'
import { protocoloLegadoFilters } from './filters.ts'
import { lerProtocolo } from './protocolo.ts'

// O dashboard Protocolo (banco legado: NG e RJ no banco NG, LA no banco LA), com os gráficos da v1.
export const protocolo: DashboardModule<V1GenericoResponse> = {
    key: 'protocolo',
    fetch: (query) => dataClient.getDashboardData<V1GenericoResponse>('protocolo', query),
    Content: ProtocoloLegadoContent,
    filters: (data) => protocoloLegadoFilters(lerProtocolo(data)),
    commission: (data) => ({
        columns: [
            COL_FUNCIONARIO,
            { key: 'qtd_protocolados', label: 'Protocolados', format: fmt.int, sum: true },
            COL_COMISSAO,
        ],
        rows: lerProtocolo(data).comissao,
        sortBy: 'valor_comissao',
    }),
}
