import type { FilterField } from '../../../lib/filters.ts'
import type { PeticionamentoLexpreResponse } from './types.ts'

const toOptions = (values: string[] = []) => values.map((value) => ({ value, label: value }))

// Os filtros do Peticionamento (os mesmos da v1 e do Protocolo), com as opções que vêm na resposta.
// Ordem e nomes da v1 (Funcionários · Atuação · UF · Matéria). O LexPre ainda não traz UF nesta consulta:
// sem opções, o filtro não aparece.
export const peticionamentoFilters = (options: PeticionamentoLexpreResponse['opcoes_filtro']): FilterField[] =>
    [
        { key: 'funcionario' as const, label: 'Funcionários', options: toOptions(options?.funcionarios) },
        {
            key: 'area_atuacao_id' as const,
            label: 'Atuação',
            options: (options?.areas ?? []).map((a) => ({ value: String(a.id), label: a.nome })), // na URL vai o id
        },
        { key: 'uf' as const, label: 'UF', options: toOptions(options?.ufs) },
        { key: 'materia' as const, label: 'Matéria', options: toOptions(options?.materias) },
    ].filter((f) => f.key !== 'uf' || f.options.length > 0)
