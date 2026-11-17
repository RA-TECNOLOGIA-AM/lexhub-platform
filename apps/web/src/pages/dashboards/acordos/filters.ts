import type { FilterField } from '../../../lib/filters.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { filtrosPagina, filtrosSetor } from '../execucao/setorExecucao.ts'
import { ehAcordosNG, lerAcordosNG } from './execucaoAcordos.ts'

const opcoes = (xs: string[]) => [...new Set(xs.filter(Boolean))].map((v) => ({ value: v, label: v }))

// Os filtros dos Acordos na NG: os da página da v1 (UF, comarca, matéria, subfase, Pré/Pós-Sentença e
// Judicial/Extrajudicial), o processo clicado nas diligências (filtra a página toda) e os seletores das seções
// Atividades e Diligências. LA e RJ (tela de KPIs) não têm filtros. Só lógica pura (testada em
// execucaoAcordos.test.ts).
export function acordosFilters(data: V1GenericoResponse): FilterField[] {
    if (!ehAcordosNG(data)) return []
    const a = lerAcordosNG(data)
    return [
        ...filtrosPagina(a.opcoes),
        {
            key: 'tipo_sentenca_execucao_acordos',
            label: 'Pré x Pós-Sentença',
            options: opcoes(a.porSentenca.map((p) => p.name)),
            single: true,
        },
        {
            key: 'tipo_acao_execucao_acordos',
            label: 'Judicial x Extrajudicial',
            options: opcoes(a.porTipoAcao.map((p) => p.name)),
            single: true,
        },
        {
            key: 'numero_processo_execucao_acordos',
            label: 'Processo',
            options: opcoes(a.setor.diligencias.porProcesso.map((p) => p.processo)),
            single: true,
        },
        ...filtrosSetor('acordos', a.setor),
    ]
}
