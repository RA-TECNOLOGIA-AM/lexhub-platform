import type { FilterField } from '../../../lib/filters.ts'
import { isPlaceholder } from '../setor/setor.ts'
import { opcoesOrgDocumentos, type OrgDocumentosLegado } from './orgDocumentos.ts'

// "-" é a matéria vazia na v1: aparece no gráfico, mas não vira opção de filtro.
const toOptions = (values: string[]) =>
    values.filter((v) => !isPlaceholder(v) && v !== '-').map((value) => ({ value, label: value }))

// Os filtros da Organização de Documentos (banco legado), os da página da v1 (Funcionários · Matéria). As
// opções vêm da própria resposta, como na v1.
export function orgDocumentosLegadoFilters(p: OrgDocumentosLegado): FilterField[] {
    const o = opcoesOrgDocumentos(p)
    return [
        { key: 'funcionario', label: 'Funcionários', options: toOptions(o.funcionarios) },
        { key: 'materia', label: 'Matéria', options: toOptions(o.materias) },
    ]
}
