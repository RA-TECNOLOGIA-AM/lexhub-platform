import type { FilterField } from '../../../lib/filters.ts'
import type { ProtocoloResponse } from '../../../types/index.ts'

const toOptions = (values: string[]) => values.map((value) => ({ value, label: value }))

// Os filtros do Protocolo (os mesmos da v1), com as opções que vêm na resposta (opcoes_filtro).
export const protocoloFilters = (options: ProtocoloResponse['opcoes_filtro']): FilterField[] => [
    { key: 'materia', label: 'Matéria', options: toOptions(options.materias) },
    { key: 'funcionario', label: 'Funcionário', options: toOptions(options.funcionarios) },
    { key: 'uf', label: 'UF', options: toOptions(options.ufs) },
    {
        key: 'area_atuacao_id',
        label: 'Área de atuação',
        options: options.areas.map((a) => ({ value: String(a.id), label: a.nome })), // na URL vai o id; na tela, o nome
    },
]
