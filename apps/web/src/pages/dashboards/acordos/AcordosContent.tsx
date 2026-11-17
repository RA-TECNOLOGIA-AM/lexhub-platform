import type { ContentProps } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { AcordosKpisContent } from './AcordosKpisContent.tsx'
import { AcordosNGContent } from './AcordosNGContent.tsx'
import { ehAcordosNG } from './execucaoAcordos.ts'

// Execução Acordos: a NG (rota /execucao_acordos_NG) com a página da v1; LA e RJ, por enquanto, só com os KPIs.
export function AcordosContent(props: ContentProps<V1GenericoResponse>) {
    return ehAcordosNG(props.data) ? (
        <AcordosNGContent {...props} />
    ) : (
        <AcordosKpisContent data={{ ...props.data, stats: props.data.stats ?? {} }} />
    )
}
