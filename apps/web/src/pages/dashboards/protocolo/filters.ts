import type { FilterField } from '../../../lib/filters.ts'
import { isPlaceholder } from '../setor/setor.ts'
import { opcoesProtocolo, type ProtocoloLegado } from './protocolo.ts'

const toOptions = (values: string[]) =>
    values.filter((v) => !isPlaceholder(v)).map((value) => ({ value, label: value }))

// Os filtros do Protocolo (banco legado), os mesmos da página da v1 (Funcionários · Matéria), mais o sistema,
// que na v1 se escolhia clicando no gráfico (um só). As opções vêm da própria resposta, como na v1.
export function protocoloLegadoFilters(p: ProtocoloLegado): FilterField[] {
    const o = opcoesProtocolo(p)
    return [
        { key: 'funcionario', label: 'Funcionários', options: toOptions(o.funcionarios) },
        { key: 'materia', label: 'Matéria', options: toOptions(o.materias) },
        { key: 'sistema', label: 'Sistema', options: toOptions(o.sistemas), single: true },
    ]
}
