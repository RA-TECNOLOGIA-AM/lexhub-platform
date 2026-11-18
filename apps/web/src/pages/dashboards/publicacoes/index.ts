import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { PublicacoesContent } from './PublicacoesContent.tsx'
import { publicacoesFilters } from './filters.ts'
import { comissaoPublicacoes, type PublicacoesResponse } from './publicacoes.ts'

// Publicações (LexFlow, NG, LA e RJ, área Jurídico): a página da v1, com a comissão dos leitores.
export const publicacoes: DashboardModule<PublicacoesResponse> = {
    key: 'publicacoes',
    fetch: (query) => dataClient.getDashboardData<PublicacoesResponse>('publicacoes', query),
    Content: PublicacoesContent,
    filters: publicacoesFilters,
    commission: comissaoPublicacoes,
}
