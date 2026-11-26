import type { FilterField } from '../../../lib/filters.ts'
import { SITUACOES, UFS_NG, comarcasDisponiveis, type EstrategicoResponse } from './estrategico.ts'

const UF_LABEL: Record<string, string> = { AM: 'NGAM (AM)', PA: 'NGPA (PA)', PB: 'NGPB (PB)' }

// Os filtros da página da v1, por unidade: na NG o escritório (NGAM/NGPA/NGPB) vira a UF; comarca e situação valem
// só para o Jurídico (seções 03 e 04), como na v1. A comarca também se liga clicando no gráfico por comarca.
export function estrategicoFilters(data: EstrategicoResponse): FilterField[] {
    return [
        ...(data.tem_uf
            ? [
                  {
                      key: 'uf_estrategico' as const,
                      label: 'Escritório (UF)',
                      options: UFS_NG.map((u) => ({ value: u, label: UF_LABEL[u] })),
                  },
              ]
            : []),
        {
            key: 'comarca_estrategico',
            label: 'Comarca (Jurídico)',
            options: comarcasDisponiveis(data).map((c) => ({ value: c, label: c })),
        },
        { key: 'situacao_estrategico', label: 'Situação (Jurídico)', options: SITUACOES },
    ]
}
