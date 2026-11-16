import { fmt } from '../../../lib/format.ts'
import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { comercialExport } from '../comercial-lexpre/exportFields.ts'
import { comercialFilters } from '../comercial-lexpre/filters.ts'
import { ComissaoLexpreContent } from './ComissaoLexpreContent.tsx'
import type { ComissaoLexpreResponse } from './types.ts'

// O dashboard Comissão Comercial (LexPre): de onde vêm os dados e como mostrar.
export const comissaoLexpre: DashboardModule<ComissaoLexpreResponse> = {
    key: 'comissao-lexpre',
    fetch: (query) => dataClient.getDashboardData<ComissaoLexpreResponse>('comissao-lexpre', query),
    Content: ComissaoLexpreContent,
    filters: comercialFilters,
    // O relatório do Comercial (colunas da query), só com os próprios dados para quem não gere a unidade.
    exportFields: comercialExport,
    // "Gerar comissão": mesmas colunas e ordem do PDF da v1 (ComissionamentoPdf.ts).
    commission: (data) => ({
        columns: [
            { key: 'atendente', label: 'Atendentes' },
            { key: 'acoes', label: 'Ações', format: fmt.int, sum: true },
            { key: 'comissao_base', label: 'Comissão base', format: fmt.brl, sum: true },
            { key: 'valor_fm', label: 'Valor FM', format: fmt.brl, sum: true },
            { key: 'proporcional_am_pa', label: 'Proporcional AM/PA', format: fmt.brl, sum: true },
            { key: 'proporcional_pb', label: 'Proporcional PB', format: fmt.brl, sum: true },
            { key: 'comissao_com_fm', label: 'Comissão com FM', format: fmt.brl, sum: true },
            { key: 'desconto_cancelamentos', label: 'Desconto (cancelamento)', format: fmt.brl, sum: true },
        ],
        rows: data.stats.comissionamento_por_atendente ?? [],
        sortBy: 'comissao_com_fm',
    }),
}
