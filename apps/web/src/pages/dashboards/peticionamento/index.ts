import { COL_COMISSAO, COL_FUNCIONARIO } from '../../../lib/commissionReport.ts'
import { fmt } from '../../../lib/format.ts'
import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { PeticionamentoLegadoContent } from './PeticionamentoLegadoContent.tsx'
import { peticionamentoLegadoFilters } from './filters.ts'
import { lerPeticionamento } from './peticionamento.ts'

// O dashboard Peticionamento (banco legado: NG e RJ no banco NG), com os gráficos da v1.
export const peticionamento: DashboardModule<V1GenericoResponse> = {
    key: 'peticionamento',
    fetch: (query) => dataClient.getDashboardData<V1GenericoResponse>('peticionamento', query),
    Content: PeticionamentoLegadoContent,
    filters: (data) => peticionamentoLegadoFilters(lerPeticionamento(data)),
    // Mesmas colunas do PDF da v1: taxa (define a faixa de preço), Massa e ESPECÍFICA (qtd × valor) e comissão.
    commission: (data) => ({
        columns: [
            COL_FUNCIONARIO,
            { key: 'taxa_resolvidos', label: 'Taxa resolvidos', format: fmt.pct },
            { key: 'qtd_acoes_massa', label: 'Qtd Massa', format: fmt.int, sum: true },
            { key: 'valor_acoes_massa', label: 'R$/Massa', format: fmt.brl },
            { key: 'qtd_x_valor_massa', label: 'Total Massa', format: fmt.brl, sum: true },
            { key: 'qtd_acoes_especificas', label: 'Qtd Específica', format: fmt.int, sum: true },
            { key: 'valor_acoes_especificas', label: 'R$/Específica', format: fmt.brl },
            { key: 'qtd_x_valor_especificas', label: 'Total Específica', format: fmt.brl, sum: true },
            COL_COMISSAO,
        ],
        rows: lerPeticionamento(data).comissao,
        sortBy: 'valor_comissao',
    }),
}
