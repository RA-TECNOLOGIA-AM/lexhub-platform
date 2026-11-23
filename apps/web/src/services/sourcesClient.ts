import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import type { Http } from './http.ts'
import { createRpc } from './rpc.ts'
import type {
    ConnectInfo,
    ConnectResult,
    DataSource,
    ProductOffices,
    SheetTab,
    SourceDetail,
    SourcesFreshness,
    SourcesResponse,
    SourceTestResult,
    UnitDeletionImpact,
    UnitInput,
    UnitSources,
} from '../types/index.ts'

type SourcesClient = Pick<
    DataClient,
    | 'getSources'
    | 'getSourceDetail'
    | 'getSourcesFreshness'
    | 'getFailingSources'
    | 'createUnit'
    | 'updateUnit'
    | 'getUnitDeletionImpact'
    | 'deleteUnit'
    | 'listProductOffices'
    | 'linkProductOffice'
    | 'getConnectInfo'
    | 'inspectSheet'
    | 'connectSource'
    | 'retestSource'
    | 'changeSourceSecret'
    | 'disconnectSource'
    | 'setSourceEnabled'
>

// Os parâmetros que create_unit e update_unit recebem (mesmos nomes do banco).
const unitArgs = (org: string, unit: UnitInput) => ({
    p_org: org,
    p_code: unit.code,
    p_name: unit.name,
    p_timezone: unit.timezone,
})

// Resposta de GET /orgs/{org}/sources/freshness (app/routes/source_freshness.py).
type FreshnessOut = {
    sources: Record<
        string,
        { fetched_at: string | null; ttl_min: number; error: string | null; error_at: string | null }
    >
}

const toFreshness = (out: FreshnessOut): SourcesFreshness =>
    Object.fromEntries(
        Object.entries(out.sources).map(([key, f]) => [
            key,
            { fetchedAt: f.fetched_at, cacheMin: f.ttl_min, error: f.error, errorAt: f.error_at },
        ]),
    )

// Módulo: Unidades e fontes. Ler e ligar escritório pelo Supabase (schema api); o que fala com o banco
// do produto ou da operação (lista de escritórios, testar e salvar, trocar senha) pela API em Python.
// As funções devolvem só o que quem chama vê (Owner/Desenvolvedor: todas as unidades; Gestor/Controller: as dele).
export function createSourcesClient(supabase: SupabaseClient, http: Http): SourcesClient {
    const call = createRpc(supabase)
    const enc = encodeURIComponent
    return {
        getSources: (org) => call<SourcesResponse>('list_sources', { p_org: org }),
        getSourceDetail: (org, unit, source) =>
            call<SourceDetail>('source_detail', { p_org: org, p_unit: unit, p_source: source }),
        getSourcesFreshness: async (org, keys) =>
            toFreshness(
                await http.get<FreshnessOut>(`/orgs/${enc(org)}/sources/freshness?keys=${enc(keys.join(','))}`),
            ),
        getFailingSources: async () => (await http.get<{ orgs: Record<string, string[]> }>('/sources/failing')).orgs,
        createUnit: (org, unit) => call<UnitSources>('create_unit', unitArgs(org, unit)),
        updateUnit: (org, unit) => call<UnitSources>('update_unit', unitArgs(org, unit)),
        getUnitDeletionImpact: (org, unit) =>
            call<UnitDeletionImpact>('unit_deletion_impact', { p_org: org, p_code: unit }),
        deleteUnit: async (org, unit, confirmName) => {
            await call<null>('delete_unit', { p_org: org, p_code: unit, p_confirm: confirmName })
        },
        listProductOffices: (product) => http.get<ProductOffices>(`/sources/${product}/offices`),
        linkProductOffice: (org, unit, product, ref) =>
            call<UnitSources>('link_product_office', { p_org: org, p_unit: unit, p_product: product, p_ref: ref }),
        getConnectInfo: () => http.get<ConnectInfo>('/sources/connect-info'),
        inspectSheet: async (url) => (await http.post<{ tabs: SheetTab[] }>('/sources/sheets/inspect', { url })).tabs,
        connectSource: (org, unit, input) =>
            http.post<ConnectResult>(`/orgs/${enc(org)}/units/${enc(unit)}/sources`, input),
        retestSource: (org, source) => http.post<SourceTestResult>(`/orgs/${enc(org)}/sources/${enc(source)}/test`),
        changeSourceSecret: (org, source, input) =>
            http.put<ConnectResult>(`/orgs/${enc(org)}/sources/${enc(source)}/secret`, input),
        disconnectSource: (org, source) => http.delete<void>(`/orgs/${enc(org)}/sources/${enc(source)}`),
        setSourceEnabled: (org, source, enabled) =>
            http.put<DataSource>(`/orgs/${enc(org)}/sources/${enc(source)}/enabled`, { enabled }),
    }
}
