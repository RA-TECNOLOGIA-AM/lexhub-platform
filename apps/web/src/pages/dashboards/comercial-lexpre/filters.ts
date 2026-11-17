import type { FilterField } from '../../../lib/filters.ts'
import { rotuloCanal } from './comercial.ts'
import type { ComercialLexpreResponse } from './types.ts'

const toOptions = (values: string[] = []) => values.map((value) => ({ value, label: value }))

// Os filtros do Comercial (os mesmos da v1): atendentes, canal de origem e rubrica (um valor só cada, como na
// v1), área de atuação e UF. As opções vêm na resposta; as rubricas, das ações fechadas do período.
export function comercialFilters(data: ComercialLexpreResponse): FilterField[] {
    const o = data.opcoes_filtro
    const rubricas = (data.stats.acoes_fechadas_por_rubrica?.total ?? []).map((p) => p.name)
    return [
        { key: 'atendente_comercial' as const, label: 'Atendentes', options: toOptions(o?.atendentes) },
        {
            key: 'segmento_comercial' as const,
            label: 'Canal',
            single: true,
            options: (o?.segmentos ?? []).map((value) => ({ value, label: rotuloCanal(value.toLowerCase()) })),
        },
        {
            key: 'area_atuacao_id' as const,
            label: 'Atuação',
            options: (o?.areas ?? []).map((a) => ({ value: String(a.id), label: a.nome })), // na URL vai o id
        },
        { key: 'uf' as const, label: 'UF', options: toOptions(o?.ufs) },
        { key: 'rubrica' as const, label: 'Rubrica', single: true, options: toOptions(rubricas) },
    ].filter((f) => f.key !== 'uf' || f.options.length > 0)
}
