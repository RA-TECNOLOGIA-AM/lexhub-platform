import { COL_FUNCIONARIO } from '../../../lib/commissionReport.ts'
import { fmt } from '../../../lib/format.ts'
import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { pendenciasExport } from './exportFields.ts'
import { PendenciasLegadoContent } from './PendenciasLegadoContent.tsx'
import { lerPendencias } from './pendencias.ts'

// O dashboard Pendências (banco legado: NG e RJ no banco NG, LA no banco LA). A página é a das Pendências
// (LexPre): a resposta da v1 é lida no mesmo formato (pendencias.ts).
export const pendencias: DashboardModule<V1GenericoResponse> = {
    key: 'pendencias',
    fetch: (query) => dataClient.getDashboardData<V1GenericoResponse>('pendencias', query),
    Content: PendenciasLegadoContent,
    exportFields: pendenciasExport,
    // Na v1, o filtro de funcionários (as opções vêm da própria resposta).
    filters: (data) => [
        {
            key: 'funcionario',
            label: 'Funcionários',
            options: (lerPendencias(data).opcoes_filtro?.funcionarios ?? []).map((value) => ({ value, label: value })),
        },
    ],
    // Mesmas colunas do PDF da v1 (as do Pendências LexPre): taxas, quantidade, R$ por resolvida e comissão.
    commission: (data) => ({
        columns: [
            COL_FUNCIONARIO,
            { key: 'taxa_resolvido', label: 'Taxa resolvido', format: fmt.pct },
            { key: 'taxa_cancelamento', label: 'Taxa cancelamento', format: fmt.pct },
            { key: 'qtd_resolvido', label: 'Resolvidas', format: fmt.int, sum: true },
            { key: 'valor', label: 'R$/resolvida', format: fmt.brl },
            { key: 'comissao', label: 'Comissão', format: fmt.brl, sum: true },
        ],
        rows: lerPendencias(data).comissionamento_pendencias_por_funcionario,
        sortBy: 'comissao',
    }),
}
