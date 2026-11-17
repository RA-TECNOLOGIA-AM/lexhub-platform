import type { ContentProps } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { ehExecucaoNG } from './execucao.ts'
import { ExecucaoKpisContent } from './ExecucaoKpisContent.tsx'
import { ExecucaoNGContent } from './ExecucaoNGContent.tsx'

// Execução Condenação: a NG (rota /execucao) com a página da v1; LA e RJ, por enquanto, só com os KPIs.
export function ExecucaoContent(props: ContentProps<V1GenericoResponse>) {
    return ehExecucaoNG(props.data) ? <ExecucaoNGContent {...props} /> : <ExecucaoKpisContent data={props.data} />
}
