import type { ContentProps } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { AcordosPagina } from './AcordosPagina.tsx'

// Execução Acordos: a página da v1 (NG, LA e RJ, pelas rotas de cada escritório).
export function AcordosContent(props: ContentProps<V1GenericoResponse>) {
    return <AcordosPagina {...props} />
}
