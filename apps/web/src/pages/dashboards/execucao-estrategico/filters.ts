import type { FilterField } from '../../../lib/filters.ts'
import { filtrosPagina } from '../execucao/setorExecucao.ts'
import {
    atividadesConfeccao,
    ESCOPOS,
    confeccao,
    distribuicoes,
    lados,
    opcoes,
    type EstrategicoResponse,
} from './estrategico.ts'

const lista = (xs: string[]) => [...new Set(xs.filter(Boolean))].map((v) => ({ value: v, label: v }))

// Os filtros da página da v1: escopo (Ambos / Condenação / Acordos), UF, comarca, matéria, subfase e o ano de
// ajuizamento (clicando nas pizzas); na Confecção CS, atividade e funcionário (clicando nos gráficos) e a situação.
export function estrategicoFilters(data: EstrategicoResponse): FilterField[] {
    if (!data.condenacao) return []
    const cs = confeccao(data)
    const anos = distribuicoes(lados(data, 'ambos')).anoTotal.map((a) => a.name)
    return [
        { key: 'escopo', label: 'Escopo', options: ESCOPOS.filter((e) => e.value !== 'ambos'), single: true },
        ...filtrosPagina(opcoes(data)),
        { key: 'ano_ajuizamento', label: 'Ano de ajuizamento', options: lista(anos), single: true },
        {
            key: 'atividade_execucao',
            label: 'Atividade (Confecção CS)',
            options: lista(atividadesConfeccao(data)),
            single: true,
            fromChart: true,
        },
        {
            key: 'funcionario_execucao',
            label: 'Funcionário (Confecção CS)',
            options: lista(cs.funcionarios),
            fromChart: true,
        },
        {
            key: 'situacao_execucao',
            label: 'Situação (Confecção CS)',
            options: cs.situacoes.map((s) => ({ value: s.id, label: s.label })),
        },
    ]
}
