import type { FilterField } from '../../../lib/filters.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import { SITUACOES } from '../julgados-acordaos/filters.ts'
import { lerRecursal, type RecursalResponse } from './recursal.ts'

const lista = (xs: string[]) => [...new Set(xs.filter(Boolean))].map((v) => ({ value: v, label: v }))
// O que já está escolhido continua na lista, mesmo sem aparecer nas opções de agora.
const com = (opcoes: { value: string; label: string }[], escolhidos: string[] = []) => [
    ...opcoes,
    ...escolhidos.filter((v) => !opcoes.some((o) => o.value === v)).map((v) => ({ value: v, label: v })),
]

// Os filtros da página da v1, na ordem do painel dela: os dos processos (cumulativos: E entre campos, OU dentro de
// um), os da seção Atividades (agendamentos do setor RECURSOS) e a situação do processo.
export function recursalFilters(data: RecursalResponse, f: DashboardFilters = {}): FilterField[] {
    const r = lerRecursal(data)
    if (!r.temDados) return []
    const o = r.opcoes
    return [
        { key: 'id_1g_recursal', label: 'Status 1º grau', options: com(o.status1g, f.id_1g_recursal) },
        { key: 'id_2g_recursal', label: 'Status 2º grau', options: com(o.status2g, f.id_2g_recursal) },
        { key: 'decisao_recursal', label: 'Decisões', options: com(o.decisoes, f.decisao_recursal) },
        { key: 'juiz_recursal', label: 'Juiz', options: com(lista(o.juizes), f.juiz_recursal) },
        { key: 'relator_recursal', label: 'Relator', options: com(lista(o.relatores), f.relator_recursal) },
        { key: 'materia_recursal', label: 'Matéria', options: com(lista(o.materias), f.materia_recursal) },
        {
            key: 'competencia_recursal',
            label: 'Competência',
            options: com(lista(o.competencias), f.competencia_recursal),
        },
        { key: 'vara_recursal', label: 'Vara', options: com(lista(o.varas), f.vara_recursal) },
        { key: 'subfase_recursal', label: 'Subfase', options: com(lista(o.subfases), f.subfase_recursal) },
        { key: 'extinto_2g_recursal', label: 'Extintos 2º grau', options: com(o.extintos, f.extinto_2g_recursal) },
        {
            key: 'funcionario_recursos',
            label: 'Funcionários (Atividades)',
            options: com(lista(r.opcoesLista.funcionarios), f.funcionario_recursos),
        },
        {
            key: 'atividade_recursos',
            label: 'Atividades',
            options: com(lista(r.opcoesLista.atividades), f.atividade_recursos),
        },
        {
            key: 'situacao_recursos',
            label: 'Situação (Atividades)',
            options: com(
                r.opcoesLista.situacoes.map((s) => ({ value: s.id, label: s.label })),
                f.situacao_recursos,
            ),
        },
        {
            key: 'status_recursos',
            label: 'Status (Atividades)',
            options: com(lista(r.opcoesLista.status), f.status_recursos),
        },
        { key: 'situacao_processo', label: 'Situação do processo', options: SITUACOES },
    ]
}
