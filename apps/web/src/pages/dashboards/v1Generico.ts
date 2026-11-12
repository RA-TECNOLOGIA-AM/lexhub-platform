import type { ComponentType } from 'react'
import { dataClient } from '../../services/client.ts'
import type { DashboardModule } from './types.ts'
import type { V1GenericoResponse } from './v1Stats.ts'

// Módulo de um dashboard genérico do NG: a key do catálogo/API e o miolo da página.
// A resposta e o leitor de `stats` ficam em v1Stats.ts (lógica pura, sem o cliente de dados).
export function v1GenericoModule(
    key: string,
    Content: ComponentType<{ data: V1GenericoResponse }>,
): DashboardModule<V1GenericoResponse> {
    return {
        key,
        fetch: (query) => dataClient.getDashboardData<V1GenericoResponse>(key, query),
        Content,
    }
}
