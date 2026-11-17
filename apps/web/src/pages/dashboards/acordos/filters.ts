import type { FilterField } from '../../../lib/filters.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { filtrosPagina, filtrosSetor } from '../execucao/setorExecucao.ts'
import { lerAcordos } from './execucaoAcordos.ts'
import { unidadeAcordos } from '../execucao/unidade.ts'

const opcoes = (xs: string[]) => [...new Set(xs.filter(Boolean))].map((v) => ({ value: v, label: v }))

// Os filtros da Execução Acordos (NG, LA e RJ): os da página da v1 (UF, comarca, matéria, subfase, Pré/Pós-Sentença e
// Judicial/Extrajudicial), o processo clicado nas diligências (filtra a página toda) e os seletores das seções
// Atividades e Diligências. Sem a rota da v1 na resposta (mock sem dados): nenhum. Só lógica pura (testada em
// execucaoAcordos.test.ts).
export function acordosFilters(data: V1GenericoResponse): FilterField[] {
    if (!unidadeAcordos(data)) return []
    const a = lerAcordos(data)
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
