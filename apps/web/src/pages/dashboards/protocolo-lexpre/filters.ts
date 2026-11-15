import type { FilterField } from '../../../lib/filters.ts'
import type { ProtocoloResponse } from '../../../types/index.ts'

const toOptions = (values: string[]) => values.map((value) => ({ value, label: value }))

// Os filtros do Protocolo (os mesmos da v1), com as opções que vêm na resposta (opcoes_filtro).
// Ordem e nomes da v1 (Funcionários · Atuação · UF · Matéria).
export const protocoloFilters = (options: ProtocoloResponse['opcoes_filtro']): FilterField[] => [
    { key: 'funcionario', label: 'Funcionários', options: toOptions(options.funcionarios) },
    {
        key: 'area_atuacao_id',
        label: 'Atuação',
        options: options.areas.map((a) => ({ value: String(a.id), label: a.nome })), // na URL vai o id; na tela, o nome
    },
    { key: 'uf', label: 'UF', options: toOptions(options.ufs) },
    { key: 'materia', label: 'Matéria', options: toOptions(options.materias) },
]
