import type { FilterField } from '../../../lib/filters.ts'
import { isPlaceholder } from '../setor/setor.ts'
import { opcoesPeticionamento, type PeticionamentoLegado } from './peticionamento.ts'

const toOptions = (values: string[]) =>
    values.filter((v) => !isPlaceholder(v)).map((value) => ({ value, label: value }))

// Os filtros do Peticionamento (banco legado), os da página da v1 (Funcionários · Matéria). As opções vêm da
// própria resposta, como na v1.
export function peticionamentoLegadoFilters(p: PeticionamentoLegado): FilterField[] {
    const o = opcoesPeticionamento(p)
    return [
        { key: 'funcionario', label: 'Funcionários', options: toOptions(o.funcionarios) },
        { key: 'materia', label: 'Matéria', options: toOptions(o.materias) },
    ]
}
