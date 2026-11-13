import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import { createRpc } from './rpc.ts'
import type { SourceDetail, SourcesResponse, UnitInput, UnitSources } from '../types/index.ts'

type SourcesClient = Pick<DataClient, 'getSources' | 'getSourceDetail' | 'createUnit' | 'updateUnit'>

// Os parâmetros que create_unit e update_unit recebem (mesmos nomes do banco).
const unitArgs = (org: string, unit: UnitInput) => ({
    p_org: org,
    p_code: unit.code,
    p_name: unit.name,
    p_timezone: unit.timezone,
})

// Módulo: Unidades e fontes pelo Supabase (schema api, sem a API em Python).
// As funções devolvem só o que quem chama vê (Owner/Desenvolvedor: todas as unidades; Gestor/Controller: as dele).
export function createSourcesClient(supabase: SupabaseClient): SourcesClient {
    const call = createRpc(supabase)
    return {
        getSources: (org) => call<SourcesResponse>('list_sources', { p_org: org }),
        getSourceDetail: (org, unit, source) =>
            call<SourceDetail>('source_detail', { p_org: org, p_unit: unit, p_source: source }),
        createUnit: (org, unit) => call<UnitSources>('create_unit', unitArgs(org, unit)),
        updateUnit: (org, unit) => call<UnitSources>('update_unit', unitArgs(org, unit)),
    }
}
