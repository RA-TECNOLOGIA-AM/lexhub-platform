import type { ContentProps } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { PendenciasContent } from '../pendencias-lexpre/PendenciasContent.tsx'
import { lerPendencias } from './pendencias.ts'

// As Pendências do banco legado (NG, RJ e LA): a mesma página das Pendências (LexPre), com a resposta da v1
// lida no formato dela.
export function PendenciasLegadoContent({ data, ...rest }: ContentProps<V1GenericoResponse>) {
    return <PendenciasContent data={lerPendencias(data)} {...rest} />
}
