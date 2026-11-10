import { dataClient } from '../../services/client.ts'
import type { Meta } from '../../types/index.ts'
import { BaseContent } from './BaseContent.tsx'
import { baseMeta } from './baseView.ts'
import type { DashboardModule } from './types.ts'

export type BaseResponse = { meta: Meta }

// Módulo: cria a página-base de qualquer dashboard pela key (mesmo DashboardView, cabeçalho de verdade).
// Quando o conteúdo ficar pronto, o dashboard troca baseModule('key') por { key, fetch, Content } próprios.
export function baseModule(key: string): DashboardModule<BaseResponse> {
    return {
        key,
        fetch: async ({ org, unit }) => ({ meta: baseMeta(await dataClient.listDashboards(org), key, unit) }),
        Content: BaseContent,
    }
}
