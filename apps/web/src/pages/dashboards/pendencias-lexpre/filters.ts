import type { FilterField } from '../../../lib/filters.ts'
import type { PendenciasResponse } from '../../../types/index.ts'

const toOptions = (values: string[] = []) => values.map((value) => ({ value, label: value }))

// Os filtros de Pendências (os mesmos da v1: sem matéria), com as opções que vêm na resposta.
// Ordem e nomes dos outros dashboards (Funcionários · Atuação · UF). UF sem opções não aparece.
export const pendenciasFilters = (options: PendenciasResponse['opcoes_filtro']): FilterField[] =>
    [
        { key: 'funcionario' as const, label: 'Funcionários', options: toOptions(options?.funcionarios) },
        {
            key: 'area_atuacao_id' as const,
            label: 'Atuação',
            options: (options?.areas ?? []).map((a) => ({ value: String(a.id), label: a.nome })), // na URL vai o id
        },
        { key: 'uf' as const, label: 'UF', options: toOptions(options?.ufs) },
    ].filter((f) => f.key !== 'uf' || f.options.length > 0)
