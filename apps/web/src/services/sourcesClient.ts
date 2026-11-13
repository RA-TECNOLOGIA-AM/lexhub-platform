import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { createRpc } from './rpc.ts'
import type { SourcesResponse } from '../types/index.ts'

type SourcesClient = Pick<DataClient, 'getSources'>

// Módulo: Unidades e fontes pelo Supabase (api.list_sources, sem a API em Python).
// A função devolve só as unidades que quem chama vê (Owner/Desenvolvedor: todas; Gestor/Controller: as dele).
export function createSourcesClient(supabase: SupabaseClient): SourcesClient {
    const call = createRpc(supabase)
    return {
        getSources: (org) => call<SourcesResponse>('list_sources', { p_org: org }),
    }
}
