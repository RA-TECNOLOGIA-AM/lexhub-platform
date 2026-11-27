import { describe, expect, it } from 'vitest'
import { fakeSupabase } from './fakeSupabase.ts'
import { createApiKeysClient } from './apiKeysClient.ts'
import type { Http } from './http.ts'

function fakeHttp(result: unknown) {
    const posts: { path: string; body: unknown }[] = []
    const http = {
        post: async (path: string, body?: unknown) => {
            posts.push({ path, body })
            return result
        },
    } as unknown as Http
    return { http, posts }
}

const ROW = {
    id: 'k1',
    user_name: 'Ana',
    user_email: 'ana@x.com',
    status: 'active',
    note: null,
    decision_note: null,
    requested_at: '2026-11-26T12:00:00Z',
    decided_at: '2026-11-26T13:00:00Z',
    revoked_at: null,
    last_used_at: null,
    last_used_ip: '10.0.0.5',
    sectors: [
        { setor: 'Comercial', base: true, status: 'approved' },
        {
            setor: 'Protocolo',
            base: false,
            status: 'approved',
            justificativa: 'Automação de metas',
            expires_at: '2027-02-24T03:00:00Z',
        },
    ],
}

describe('createApiKeysClient', () => {
    it('chama as funções certas no schema api com os parâmetros certos', async () => {
        const { supabase, calls } = fakeSupabase({ data: [] })
        const client = createApiKeysClient(supabase, fakeHttp({}).http)
        await client.getApiKeyEligibility('lexgroup')
        await client.requestApiKey('lexgroup', 'Power BI', [
            { setor: 'Protocolo', justificativa: 'Automação de metas', validade: '2027-02-24' },
        ])
        await client.getMyApiKey('lexgroup')
        await client.listApiKeys('lexgroup', 'pending')
        await client.countPendingApiKeys('lexgroup')
        await client.decideApiKey('k1', true, ['Protocolo'], null)
        await client.revokeApiKey('k1')
        await client.revokeApiKeySector('k1', 'Protocolo')
        expect(calls.every((c) => c.schema === 'api')).toBe(true)
        expect(calls.map((c) => [c.fn, c.args])).toEqual([
            ['api_key_eligibility', { p_org: 'lexgroup' }],
            [
                'request_api_key',
                {
                    p_org: 'lexgroup',
                    p_note: 'Power BI',
                    p_extras: [{ setor: 'Protocolo', justificativa: 'Automação de metas', validade: '2027-02-24' }],
                },
            ],
            ['my_api_key', { p_org: 'lexgroup' }],
            ['list_api_keys', { p_org: 'lexgroup', p_status: 'pending' }],
            ['count_pending_api_keys', { p_org: 'lexgroup' }],
            ['decide_api_key', { p_key: 'k1', p_approve: true, p_sectors_approved: ['Protocolo'], p_note: null }],
            ['revoke_api_key', { p_key: 'k1' }],
            ['revoke_api_key_sector', { p_key: 'k1', p_sector: 'Protocolo' }],
        ])
    })

    it('converte a chave para o formato da tela', async () => {
        const { supabase } = fakeSupabase({ data: ROW })
        const key = await createApiKeysClient(supabase, fakeHttp({}).http).getMyApiKey('lexgroup')
        expect(key).toEqual({
            id: 'k1',
            userName: 'Ana',
            userEmail: 'ana@x.com',
            status: 'active',
            note: null,
            decisionNote: null,
            requestedAt: '2026-11-26T12:00:00Z',
            decidedAt: '2026-11-26T13:00:00Z',
            revokedAt: null,
            lastUsedAt: null,
            lastUsedIp: '10.0.0.5',
            sectors: [
                { setor: 'Comercial', base: true, status: 'approved', justificativa: null, expiresAt: null },
                {
                    setor: 'Protocolo',
                    base: false,
                    status: 'approved',
                    justificativa: 'Automação de metas',
                    expiresAt: '2027-02-24T03:00:00Z',
                },
            ],
        })
    })

    it('sem chave: getMyApiKey devolve null; elegibilidade vem em camelCase', async () => {
        expect(
            await createApiKeysClient(fakeSupabase({ data: null }).supabase, fakeHttp({}).http).getMyApiKey('x'),
        ).toBeNull()
        const { supabase } = fakeSupabase({
            data: { eligible: true, base_sectors: ['Comercial'], sectors: ['Comercial', 'Protocolo'] },
        })
        expect(await createApiKeysClient(supabase, fakeHttp({}).http).getApiKeyEligibility('x')).toEqual({
            eligible: true,
            baseSectors: ['Comercial'],
            sectors: ['Comercial', 'Protocolo'],
        })
    })

    it('gerar tokens chama a API em Python', async () => {
        const { http, posts } = fakeHttp({
            access_token: 'a',
            access_expires_at: '2026-12-03T12:00:00Z',
            refresh_token: 'lxr_b',
            refresh_expires_at: '2026-12-26T12:00:00Z',
            token_type: 'Bearer',
        })
        const tokens = await createApiKeysClient(fakeSupabase({}).supabase, http).issueApiKeyTokens('lexgroup')
        expect(posts).toEqual([{ path: '/orgs/lexgroup/api-key/tokens', body: undefined }])
        expect(tokens).toEqual({
            accessToken: 'a',
            accessExpiresAt: '2026-12-03T12:00:00Z',
            refreshToken: 'lxr_b',
            refreshExpiresAt: '2026-12-26T12:00:00Z',
        })
    })
})
