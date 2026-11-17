import type { FilterField } from '../../../lib/filters.ts'
import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { FinanceiroEstrategicoContent } from './FinanceiroEstrategicoContent.tsx'
import { OPCOES_MES } from './financeiroEstrategico.ts'
import type { FinanceiroEstrategicoResponse } from './types.ts'

const opcoes = (xs: string[] = []) => xs.map((value) => ({ value, label: value }))

// Os filtros da v1 (Origem · Matérias · Ano de ajuizamento) e, como `inline` (ficam na própria seção ou modal,
// não na janela Filtros), os seletores de ano da Conversão e de ano/mês do modal de Clientes Pendentes.
function filtros(d: FinanceiroEstrategicoResponse): FilterField[] {
    const o = d.reflexo_financeiro?.filtros_opcoes
    return [
        { key: 'origem', label: 'Origem', options: opcoes(o?.origens) },
        { key: 'materia', label: 'Matérias', options: opcoes(o?.materias) },
        { key: 'ano_ajuizamento', label: 'Ano de ajuizamento', options: opcoes(o?.anos_ajuizamento) },
        {
            key: 'conv_ano_ajuizamento',
            label: 'Conversão · ajuizamento',
            options: opcoes(d.conversao?.anos_ajuizamento_opcoes),
            inline: true,
        },
        {
            key: 'conv_ano_financeiro',
            label: 'Conversão · financeiro',
            options: opcoes(d.conversao?.anos_financeiro_opcoes),
            inline: true,
        },
        { key: 'pend_ano', label: 'Pendentes · ano', options: opcoes(d.clientes_pendentes?.anos_opcoes), inline: true },
        { key: 'pend_mes', label: 'Pendentes · mês', options: OPCOES_MES, inline: true },
    ]
}

// O dashboard Financeiro Estratégico (Financeiro; planilha do financeiro da unidade + valor ajuizado no LexFlow).
export const financeiroEstrategico: DashboardModule<FinanceiroEstrategicoResponse> = {
    key: 'financeiro-estrategico',
    fetch: (query) => dataClient.getDashboardData<FinanceiroEstrategicoResponse>('financeiro-estrategico', query),
    Content: FinanceiroEstrategicoContent,
    filters: filtros,
}
