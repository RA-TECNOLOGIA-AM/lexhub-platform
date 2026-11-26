import type { FilterField } from '../../../lib/filters.ts'
import { STATUS_META, rankingProblemas, setores, type VinculacoesResponse } from './vinculacoes.ts'

const STATUS_OPCOES = [
    { value: 'erro', label: STATUS_META.erro.label },
    { value: 'incompleta', label: STATUS_META.incompleta.label },
    { value: 'ok', label: STATUS_META.ok.label },
    { value: 'inativa', label: 'Inativas' },
    { value: 'todas', label: 'Todas (inclui inativas)' },
]

// Os filtros da página da v1 (menos o escritório: a unidade já é o escritório), um valor de cada. Sem status = as
// ativas, como a v1. O tipo de problema só se liga clicando em "O que precisa de ajuste" (fromChart).
export function vinculacoesFilters(data: VinculacoesResponse): FilterField[] {
    const rows = data.rows ?? []
    return [
        {
            key: 'setor_vinculacao',
            label: 'Setor',
            options: setores(rows).map((s) => ({ value: s, label: s })),
            single: true,
        },
        { key: 'status_vinculacao', label: 'Status', options: STATUS_OPCOES, single: true },
        {
            key: 'problema_vinculacao',
            label: 'Problema',
            options: rankingProblemas(rows).map((p) => ({ value: p.tipo, label: p.tipo })),
            single: true,
            fromChart: true,
        },
    ]
}
