import type { ContentProps } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { ExecucaoPagina } from './ExecucaoPagina.tsx'

// Execução Condenação: a página da v1 (NG, LA e RJ, pelas rotas de cada escritório).
export function ExecucaoContent(props: ContentProps<V1GenericoResponse>) {
    return <ExecucaoPagina {...props} />
}
