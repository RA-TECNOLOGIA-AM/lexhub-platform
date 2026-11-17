import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { ExecucaoContent } from './ExecucaoContent.tsx'
import { ehExecucaoNG, lerExecucaoNG } from './execucao.ts'
import { filtrosPagina, filtrosSetor } from './setorExecucao.ts'

// O dashboard Execução Condenação (LexFlow): de onde vêm os dados e como mostrar. Na NG, os filtros da página
// da v1 (UF, comarca, matéria, subfase) e os seletores das seções Atividades e Diligências.
export const execucao: DashboardModule<V1GenericoResponse> = {
    key: 'execucao',
    fetch: (query) => dataClient.getDashboardData<V1GenericoResponse>('execucao', query),
    Content: ExecucaoContent,
    filters: (data) => {
        if (!ehExecucaoNG(data)) return []
        const e = lerExecucaoNG(data)
        return [...filtrosPagina(e.opcoes), ...filtrosSetor('condenacao', e.setor)]
    },
}
