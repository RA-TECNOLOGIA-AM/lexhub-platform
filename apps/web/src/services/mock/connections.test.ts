import { describe, expect, it } from 'vitest'
import type { SourcesResponse } from '../../types/index.ts'
import { DataError } from '../errors.ts'
import { catalog } from './catalog.ts'
import {
    adsOptionsIn,
    adsSummaryIn,
    changeSecretIn,
    connectIn,
    disconnectIn,
    readAdsTokenIn,
    requireSourceOn,
    retestIn,
    saveAdsSettingsIn,
    setEnabledIn,
} from './connections.ts'
import { sourceDetailFor } from './sourceDetail.ts'
import { sources } from './sources.ts'

const fresh = (): SourcesResponse => structuredClone(sources)

describe('ligar/desligar fonte no mock (mesmas regras da API)', () => {
    it('desligar: status Desligada, o dashboard da planilha responde 423; religar volta sem novo link', () => {
        const data = fresh()
        expect(setEnabledIn(data, 'sheets_financeiro_ng', false).status).toBe('disabled')
        const detail = sourceDetailFor(data, catalog, 'NG', 'sheets_financeiro_ng')!
        expect(detail.enabled).toBe(false)
        expect(() => requireSourceOn('meta-anual', 'NG')).toThrowError(
            expect.objectContaining({ status: 423 }) as DataError,
        )
        expect(() => requireSourceOn('meta-anual', 'LA_AM')).not.toThrow() // a LA segue ligada

        expect(setEnabledIn(data, 'sheets_financeiro_ng', true).status).toBe('late') // o status de antes
        expect(() => requireSourceOn('meta-anual', 'NG')).not.toThrow()
    })

    it('planilha antiga (inteira) não desconecta: desliga-se', () => {
        expect(() => disconnectIn(fresh(), 'sheets_financeiro_la')).toThrowError(/desligue em vez de desconectar/)
    })

    it('produto Lex e banco interno não ligam/desligam pela tela', () => {
        expect(() => setEnabledIn(fresh(), 'lexpre', false)).toThrowError(/não é gerenciada pela tela/)
        expect(() => setEnabledIn(fresh(), 'ng', false)).toThrowError(/não é gerenciada pela tela/)
    })

    it('detalhe técnico: a chave e a estrutura salva no teste; nunca o segredo', () => {
        const data = fresh()
        const res = connectIn(data, 'NG', {
            connector: 'postgres',
            name: 'Banco NG',
            host: 'db.operacao.com.br',
            port: null,
            database: 'operacao',
            user: 'lexhub_leitura',
            password: 's3nh@',
            ssl: true,
            writerAck: false,
        })
        const detail = sourceDetailFor(data, catalog, 'NG', res.source!.id)!
        expect(detail.technical?.key).toBe(res.source!.id)
        expect(Object.keys(detail.technical?.schema ?? {})).toContain('public.processo')
        expect(JSON.stringify(detail)).not.toContain('s3nh@')
    })
})

describe('Facebook Ads no mock (mesmas regras da API)', () => {
    const input = {
        connector: 'facebook_ads' as const,
        name: 'Anúncios NG',
        adAccountId: '123456',
        token: 'EAAB' + 'x'.repeat(40),
        settings: {
            metrics: ['reach' as const],
            conversions: ['lead'],
            campaigns: null,
            breakdowns: [],
            backfillDays: 1095 as const,
            creatives: true,
        },
    }

    it('conecta com a conta normalizada, ícone de anúncios e o token fora do detalhe', () => {
        const data = fresh()
        const res = connectIn(data, 'NG', input)
        expect(res.saved).toBe(true)
        expect(res.checks.map((c) => c.key)).toEqual(['network', 'login', 'read', 'account'])
        expect(res.source).toMatchObject({ connector: 'facebook_ads', kind: 'ads' })
        expect(res.source!.id).toMatch(/^fb_ng_/)
        const detail = sourceDetailFor(data, catalog, 'NG', res.source!.id)!
        expect(detail.config.ad_account_id).toBe('act_123456')
        expect(Object.keys(detail.technical?.schema ?? {})).toContain('app.facebook_ads_breakdowns')
        expect(detail.config.backfill_days).toBe(1095)
        expect(detail.ads?.entities?.campaigns).toBe(5)
        expect(JSON.stringify(detail)).not.toContain(input.token)
        expect(retestIn(res.source!.id).ok).toBe(true)
    })

    it('token errado não grava; conta desativada é só aviso; trocar token testa o novo', () => {
        const data = fresh()
        const bad = connectIn(data, 'NG', { ...input, token: 'errado' })
        expect(bad.saved).toBe(false)
        expect(bad.checks.find((c) => c.key === 'login')?.ok).toBe(false)
        const off = connectIn(data, 'NG', { ...input, adAccountId: 'act_9990' })
        expect(off.saved).toBe(true)
        expect(off.checks.find((c) => c.key === 'account')?.severity).toBe('warn')
        expect(changeSecretIn(data, off.source!.id, { token: 'errado', writerAck: false }).saved).toBe(false)
        expect(changeSecretIn(data, off.source!.id, { token: 'EAAC' + 'y'.repeat(40), writerAck: false }).saved).toBe(
            true,
        )
    })

    it('ler o token traz as contas com o nome e o que ele permite', () => {
        const info = readAdsTokenIn('EAAB' + 'x'.repeat(40))
        expect(info.ok).toBe(true)
        expect(info.accounts.map((a) => a.name)).toContain('NG · Captação Previdenciária')
        expect(info.capabilities.find((c) => c.key === 'insights')?.status).toBe('used')
        expect(readAdsTokenIn('EAABerrado' + 'x'.repeat(30)).ok).toBe(false)
        expect(readAdsTokenIn('EAABsemconta' + 'x'.repeat(30)).accounts).toEqual([])
        expect(
            readAdsTokenIn('EAABgerencia' + 'x'.repeat(30)).capabilities.find((c) => c.key === 'manage')?.status,
        ).toBe('warn')
    })

    it('personalizar: só conversões não refaz o histórico; detalhamento novo refaz', () => {
        const data = fresh()
        const res = connectIn(data, 'NG', { ...input, adAccountId: 'act_1234567891' })
        const id = res.source!.id
        expect(res.source!.detail).toBe('Facebook Ads · NG · Captação Previdenciária (act_1234567891)')
        const current = adsOptionsIn(id).settings!
        const conv = saveAdsSettingsIn(data, id, { ...current, conversions: ['lead', 'link_click'] })
        expect(conv.recollect).toBe(false)
        const more = saveAdsSettingsIn(data, id, { ...current, breakdowns: ['region'] })
        expect(more.recollect).toBe(true)
        expect(adsOptionsIn(id).settings!.breakdowns).toEqual(['region'])
        expect(adsSummaryIn(id)?.backfill?.done).toBe(false) // acabou de recomeçar o histórico
    })
})
