import { describe, expect, it } from 'vitest'
import {
    adsSourceName,
    CONVERSATION,
    DEFAULT_ADS_SETTINGS,
    costPer,
    count,
    cpm,
    ctr,
    dateLabel,
    defaultConversions,
    describeSettings,
    needsRecollect,
    objectiveLabel,
    segmentLabel,
    settingsFromConfig,
    settingsProblem,
    statusLabel,
    toggle,
} from './facebookAds.ts'

describe('facebookAds', () => {
    it('lê a personalização da config; fonte antiga ou campo faltando = o padrão', () => {
        expect(settingsFromConfig({ ad_account_id: 'act_1' })).toEqual(DEFAULT_ADS_SETTINGS)
        expect(
            settingsFromConfig({
                metrics: ['video', 'xyz'],
                conversions: ['lead'],
                campaigns: ['11'],
                breakdowns: ['region', 'hora'],
                backfill_days: 365,
                creatives: false,
            }),
        ).toEqual({
            metrics: ['video'],
            conversions: ['lead'],
            campaigns: ['11'],
            breakdowns: ['region'],
            backfillDays: 365,
            creatives: false,
        })
    })

    it('conversões padrão: leads e conversas que a conta teve; senão a que mais aconteceu', () => {
        const opt = (type: string, count30: number) => ({ type, label: type, count30 })
        expect(defaultConversions([opt(CONVERSATION, 10), opt('lead', 3)])).toEqual(['lead', CONVERSATION])
        expect(defaultConversions([opt('link_click', 50), opt('lead', 0)])).toEqual(['link_click'])
        expect(defaultConversions([opt('lead', 0)])).toEqual(['lead'])
    })

    it('o que impede salvar e o que pede coletar de novo', () => {
        expect(settingsProblem(DEFAULT_ADS_SETTINGS)).toBeNull()
        expect(settingsProblem({ ...DEFAULT_ADS_SETTINGS, conversions: [] })).toMatch(/conversão/)
        expect(settingsProblem({ ...DEFAULT_ADS_SETTINGS, campaigns: [] })).toMatch(/campanha/)
        const base = DEFAULT_ADS_SETTINGS
        expect(needsRecollect(base, { ...base, conversions: ['lead'], creatives: false })).toBe(false)
        expect(needsRecollect(base, { ...base, metrics: ['reach', 'video'] })).toBe(true)
        expect(needsRecollect(base, { ...base, campaigns: ['11'] })).toBe(true)
        expect(needsRecollect(base, { ...base, backfillDays: 90 })).toBe(true)
        expect(
            needsRecollect(
                { ...base, breakdowns: ['region', 'device'] },
                { ...base, breakdowns: ['device', 'region'] },
            ),
        ).toBe(false)
    })

    it('nomes da Meta em português', () => {
        expect(segmentLabel('age_gender', ['25-34', 'female'])).toBe('25-34 · Mulheres')
        expect(segmentLabel('platform', ['instagram', 'instagram_reels'])).toBe('Instagram · Reels')
        expect(segmentLabel('device', ['android_smartphone'])).toBe('Celular Android')
        expect(segmentLabel('region', ['', ''])).toBe('Não informado')
        expect(statusLabel('ACTIVE')).toBe('Ativa')
        expect(statusLabel('NOVO_STATUS')).toBe('NOVO_STATUS')
        expect(objectiveLabel('OUTCOME_LEADS')).toBe('Cadastros')
        expect(adsSourceName('NG · Captação')).toBe('Facebook Ads · NG · Captação')
    })

    it('números: custo por, CTR, CPM e datas', () => {
        expect(costPer(100, 4)).toMatch(/25,00/)
        expect(costPer(100, 0)).toBe('—')
        expect(ctr(31, 1000)).toBe('3,10%')
        expect(ctr(1, 0)).toBe('—')
        expect(cpm(52, 10_000)).toMatch(/5,20/)
        expect(count(1234.6)).toBe('1.235')
        expect(count(null)).toBe('—')
        expect(dateLabel('2026-11-25')).toBe('25/11/2026')
        expect(toggle(['a'], 'b', true)).toEqual(['a', 'b'])
        expect(toggle(['a', 'b'], 'a', false)).toEqual(['b'])
    })

    it('o resumo da personalização', () => {
        const rows = describeSettings({ ...DEFAULT_ADS_SETTINGS, campaigns: ['1', '2'] }, (t) => t.toUpperCase())
        expect(Object.fromEntries(rows)).toMatchObject({
            Campanhas: '2 escolhidas',
            Métricas: 'Básico, Alcance e frequência',
            Detalhamentos: 'Nenhum',
            Histórico: '3 anos (máximo da Meta)',
        })
    })
})
