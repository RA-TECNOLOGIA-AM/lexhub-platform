import type { FilterField } from '../../../lib/filters.ts'
import type { OrgDocumentosLexpreResponse } from './types.ts'

const toOptions = (values: string[] = []) => values.map((value) => ({ value, label: value }))

// Os filtros da Organização de documentos (os mesmos do Protocolo), com as opções que vêm na
// resposta (opcoes_filtro). Sem opcoes_filtro (ex.: mock), os filtros aparecem sem opções.
export const orgDocumentosFilters = (options: OrgDocumentosLexpreResponse['opcoes_filtro']): FilterField[] => [
    { key: 'materia', label: 'Matéria', options: toOptions(options?.materias) },
    { key: 'funcionario', label: 'Funcionário', options: toOptions(options?.funcionarios) },
    { key: 'uf', label: 'UF', options: toOptions(options?.ufs) },
    {
        key: 'area_atuacao_id',
        label: 'Área de atuação',
        options: (options?.areas ?? []).map((a) => ({ value: String(a.id), label: a.nome })), // na URL vai o id; na tela, o nome
    },
]
