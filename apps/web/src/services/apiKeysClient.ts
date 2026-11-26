import type { SupabaseClient } from '@supabase/supabase-js'
import type { DataClient } from './client.ts'
import type { Http } from './http.ts'
import { createRpc } from './rpc.ts'
import type { ApiKeyInfo, ApiKeySector } from '../types/index.ts'

type ApiKeysClient = Pick<
    DataClient,
    | 'getApiKeyEligibility'
    | 'requestApiKey'
    | 'getMyApiKey'
    | 'issueApiKeyTokens'
    | 'listApiKeys'
    | 'countPendingApiKeys'
    | 'decideApiKey'
    | 'revokeApiKey'
    | 'revokeApiKeySector'
>

type SectorRow = {
    setor: string
    base: boolean
    status: ApiKeySector['status']
    justificativa?: string | null
    expires_at?: string | null
}
type KeyRow = {
    id: string
    user_name: string
    user_email: string
    status: ApiKeyInfo['status']
    note: string | null
    decision_note: string | null
    requested_at: string
    decided_at: string | null
    revoked_at: string | null
    last_used_at: string | null
    sectors: SectorRow[]
}
type TokensRow = {
    access_token: string
    access_expires_at: string
    refresh_token: string
    refresh_expires_at: string
}

const toKey = (r: KeyRow): ApiKeyInfo => ({
    id: r.id,
    userName: r.user_name,
    userEmail: r.user_email,
    status: r.status,
    note: r.note,
    decisionNote: r.decision_note,
    requestedAt: r.requested_at,
    decidedAt: r.decided_at,
    revokedAt: r.revoked_at,
    lastUsedAt: r.last_used_at,
    sectors: (r.sectors ?? []).map((s) => ({
        setor: s.setor,
        base: s.base,
        status: s.status,
        justificativa: s.justificativa ?? null,
        expiresAt: s.expires_at ?? null,
    })),
})

// Módulo: a chave de API. Pedido, consulta, aprovação e revogação direto no Supabase (schema api);
// os tokens saem da API em Python (só ela tem o segredo e grava o hash do refresh).
// Parâmetros: o cliente do Supabase já logado e o http da API (com o token da sessão).
export function createApiKeysClient(supabase: SupabaseClient, http: Http): ApiKeysClient {
    const call = createRpc(supabase)

    return {
        async getApiKeyEligibility(org) {
            const r = await call<{ eligible: boolean; base_sectors: string[]; sectors: string[] }>(
                'api_key_eligibility',
                { p_org: org },
            )
            return { eligible: r.eligible, baseSectors: r.base_sectors ?? [], sectors: r.sectors ?? [] }
        },
        requestApiKey: (org, note, extras) =>
            call<string>('request_api_key', { p_org: org, p_note: note, p_extras: extras }),
        async getMyApiKey(org) {
            const r = await call<KeyRow | null>('my_api_key', { p_org: org })
            return r ? toKey(r) : null
        },
        async issueApiKeyTokens(org) {
            const r = await http.post<TokensRow>(`/orgs/${encodeURIComponent(org)}/api-key/tokens`)
            return {
                accessToken: r.access_token,
                accessExpiresAt: r.access_expires_at,
                refreshToken: r.refresh_token,
                refreshExpiresAt: r.refresh_expires_at,
            }
        },
        async listApiKeys(org, status) {
            const rows = await call<KeyRow[]>('list_api_keys', { p_org: org, p_status: status })
            return (rows ?? []).map(toKey)
        },
        countPendingApiKeys: (org) => call<number>('count_pending_api_keys', { p_org: org }),
        async decideApiKey(id, approve, sectors, note) {
            const r = await call<KeyRow>('decide_api_key', {
                p_key: id,
                p_approve: approve,
                p_sectors_approved: sectors,
                p_note: note,
            })
            return toKey(r)
        },
        async revokeApiKey(id) {
            await call('revoke_api_key', { p_key: id })
        },
        async revokeApiKeySector(id, sector) {
            await call('revoke_api_key_sector', { p_key: id, p_sector: sector })
        },
    }
}
