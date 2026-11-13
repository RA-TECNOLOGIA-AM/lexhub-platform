import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { createRpc } from './rpc.ts'
import type { SourceDetail, SourcesResponse } from '../types/index.ts'

type SourcesClient = Pick<DataClient, 'getSources' | 'getSourceDetail'>

// Módulo: Unidades e fontes pelo Supabase (schema api, sem a API em Python).
// As funções devolvem só o que quem chama vê (Owner/Desenvolvedor: todas as unidades; Gestor/Controller: as dele).
export function createSourcesClient(supabase: SupabaseClient): SourcesClient {
    const call = createRpc(supabase)
    return {
        getSources: (org) => call<SourcesResponse>('list_sources', { p_org: org }),
        getSourceDetail: (org, unit, source) =>
            call<SourceDetail>('source_detail', { p_org: org, p_unit: unit, p_source: source }),
    }
}
