import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { execucaoExport } from './exportFields.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { ExecucaoContent } from './ExecucaoContent.tsx'
import { lerExecucao } from './execucao.ts'
import { unidadeExecucao } from './unidade.ts'
import { filtrosPagina, filtrosSetor } from './setorExecucao.ts'

// O dashboard Execução Condenação (LexFlow): de onde vêm os dados e como mostrar. Os filtros da página da v1 (UF, comarca, matéria, subfase) e os seletores das seções Atividades e Diligências.
export const execucao: DashboardModule<V1GenericoResponse> = {
    key: 'execucao',
    fetch: (query) => dataClient.getDashboardData<V1GenericoResponse>('execucao', query),
    exportReports: execucaoExport,
    Content: ExecucaoContent,
    filters: (data) => {
        if (!unidadeExecucao(data)) return []
        const e = lerExecucao(data)
        // A LA não tem Diligências: sem os seletores dela.
        const setor = filtrosSetor('condenacao', e.setor).filter(
            (f) => e.unidade !== 'LA' || !String(f.key).startsWith('diligencia_'),
        )
        return [...filtrosPagina(e.opcoes), ...setor]
    },
}
