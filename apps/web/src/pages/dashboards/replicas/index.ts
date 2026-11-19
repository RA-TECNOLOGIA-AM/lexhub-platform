import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { ReplicasContent } from './ReplicasContent.tsx'
import { comissaoReplicas, filtrosReplicas, type ReplicasResponse } from './replicas.ts'

// Réplicas (LexFlow, NG, LA e RJ, área Jurídico; o RJ com o cálculo do NG): a página da v1, com as duas chamadas dela numa resposta só. Sem
// exportação (a v1 não tem); comissão só no LA (R$ 1,50 por réplica concluída), como a v1 (o NG e o RJ não têm).
export const replicas: DashboardModule<ReplicasResponse> = {
    key: 'replicas',
    fetch: (query) => dataClient.getDashboardData<ReplicasResponse>('replicas', query),
    Content: ReplicasContent,
    filters: filtrosReplicas,
    commission: comissaoReplicas,
}
