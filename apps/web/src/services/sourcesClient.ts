import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import type { Http } from './http.ts'
import { createRpc } from './rpc.ts'
import type { ProductOffices, SourceDetail, SourcesResponse, UnitInput, UnitSources } from '../types/index.ts'

type SourcesClient = Pick<
    DataClient,
    'getSources' | 'getSourceDetail' | 'createUnit' | 'updateUnit' | 'listProductOffices' | 'linkProductOffice'
>

// Os parâmetros que create_unit e update_unit recebem (mesmos nomes do banco).
const unitArgs = (org: string, unit: UnitInput) => ({
    p_org: org,
    p_code: unit.code,
    p_name: unit.name,
    p_timezone: unit.timezone,
})

// Módulo: Unidades e fontes. Quase tudo pelo Supabase (schema api); a lista de escritórios do
// LexPre/LexFlow vem da API em Python, que é quem fala com o banco do produto.
// As funções devolvem só o que quem chama vê (Owner/Desenvolvedor: todas as unidades; Gestor/Controller: as dele).
export function createSourcesClient(supabase: SupabaseClient, http: Http): SourcesClient {
    const call = createRpc(supabase)
    return {
        getSources: (org) => call<SourcesResponse>('list_sources', { p_org: org }),
        getSourceDetail: (org, unit, source) =>
            call<SourceDetail>('source_detail', { p_org: org, p_unit: unit, p_source: source }),
        createUnit: (org, unit) => call<UnitSources>('create_unit', unitArgs(org, unit)),
        updateUnit: (org, unit) => call<UnitSources>('update_unit', unitArgs(org, unit)),
        listProductOffices: (product) => http.get<ProductOffices>(`/sources/${product}/offices`),
        linkProductOffice: (org, unit, product, ref) =>
            call<UnitSources>('link_product_office', { p_org: org, p_unit: unit, p_product: product, p_ref: ref }),
    }
}
