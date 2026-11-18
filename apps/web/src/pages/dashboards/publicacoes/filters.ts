import type { FilterField } from '../../../lib/filters.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import { SITUACOES } from '../julgados-acordaos/filters.ts'
import { lerPublicacoes, type PublicacoesResponse } from './publicacoes.ts'

const lista = (xs: string[]) => [...new Set(xs.filter((x) => x && x !== '—'))].map((v) => ({ value: v, label: v }))
// O que já está escolhido continua na lista (como a v1, que acumulava as matérias escolhidas).
const com = (opcoes: { value: string; label: string }[], escolhidos: string[] = []) => [
    ...opcoes,
    ...escolhidos.filter((v) => !opcoes.some((o) => o.value === v)).map((v) => ({ value: v, label: v })),
]

// Os filtros da página da v1: Leitor e Matéria (vários, na janela Filtros), os dos gráficos (um valor cada; só por
// clique e nas etiquetas, como a v1) e a situação do processo.
export function publicacoesFilters(data: PublicacoesResponse, f: DashboardFilters = {}): FilterField[] {
    const p = lerPublicacoes(data)
    if (!p.temDados) return []
    const leitores = [
        'SEM LEITOR',
        ...p.leitores.filter((l) => l !== 'SEM LEITOR').sort((a, b) => a.localeCompare(b, 'pt-BR')),
    ]
    return [
        {
            key: 'leitor_publicacoes',
            label: 'Leitor',
            options: com(
                lista(leitores).map((o) => (o.value === 'SEM LEITOR' ? { ...o, label: 'Sem leitor' } : o)),
                f.leitor_publicacoes,
            ),
        },
        {
            key: 'materia_publicacoes',
            label: 'Matéria',
            options: com(
                lista(p.porMateria.map((x) => x.name).sort((a, b) => a.localeCompare(b, 'pt-BR'))),
                f.materia_publicacoes,
            ),
        },
        {
            key: 'documento_publicacoes',
            label: 'Documento',
            options: com(lista(p.porDocumento.map((x) => x.name)), f.documento_publicacoes),
            single: true,
            fromChart: true,
        },
        {
            key: 'tribunal_publicacoes',
            label: 'Tribunal',
            options: com(lista(p.porTribunal.map((x) => x.name)), f.tribunal_publicacoes),
            single: true,
            fromChart: true,
        },
        {
            key: 'orgao_publicacoes',
            label: 'Órgão',
            options: com(lista(p.porOrgao.map((x) => x.name)), f.orgao_publicacoes),
            single: true,
            fromChart: true,
        },
        {
            key: 'atividade_agendamento_publicacoes',
            label: 'Atividade (agendamento)',
            options: com(lista(p.porAtividade.map((x) => x.name)), f.atividade_agendamento_publicacoes),
            single: true,
            fromChart: true,
        },
        {
            key: 'setor_agendamento_publicacoes',
            label: 'Setor (agendamento)',
            options: com(lista(p.porSetor.map((x) => x.name)), f.setor_agendamento_publicacoes),
            single: true,
            fromChart: true,
        },
        {
            key: 'status_agendamento_publicacoes',
            label: 'Agendamento',
            options: [
                { value: 'com', label: 'Com agendamento' },
                { value: 'sem', label: 'Sem agendamento' },
            ],
            single: true,
            fromChart: true,
        },
        { key: 'situacao_processo', label: 'Situação do processo', options: SITUACOES },
    ]
}
