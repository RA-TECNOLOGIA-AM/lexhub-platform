import { COL_COMISSAO, COL_FUNCIONARIO } from '../../../lib/commissionReport.ts'
import { fmt } from '../../../lib/format.ts'
import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { PeticionamentoLexpreContent } from './PeticionamentoLexpreContent.tsx'
import { peticionamentoExport } from './exportFields.ts'
import { peticionamentoFilters } from './filters.ts'
import type { PeticionamentoLexpreResponse } from './types.ts'

// O dashboard Peticionamento (LexPre): de onde vêm os dados e como mostrar.
export const peticionamentoLexpre: DashboardModule<PeticionamentoLexpreResponse> = {
    key: 'peticionamento-lexpre',
    fetch: (query) => dataClient.getDashboardData<PeticionamentoLexpreResponse>('peticionamento-lexpre', query),
    Content: PeticionamentoLexpreContent,
    filters: (data) => peticionamentoFilters(data.opcoes_filtro),
    exportFields: peticionamentoExport,
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
        rows: data.comissionamento_por_funcionario ?? [],
        sortBy: 'valor_comissao',
    }),
}
