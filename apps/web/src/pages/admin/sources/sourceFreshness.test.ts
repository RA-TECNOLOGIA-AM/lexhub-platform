import { describe, expect, it } from 'vitest'
import type { DataSource, SourceFreshness, UnitSources } from '../../../types/index.ts'
import { sourceWithFreshness, withFreshness } from './sourceFreshness.ts'

const NOW = Date.parse('2026-11-23T12:00:00Z')
const ago = (min: number) => new Date(NOW - min * 60_000).toISOString()

const source = (over: Partial<DataSource>): DataSource => ({
    id: 'lexflow',
    kind: 'flow',
    connector: 'lexflow',
    group: 'product',
    name: 'LexFlow',
    detail: '',
    managedBy: null,
    syncedAt: null,
    rows: null,
    failures: 0,
    status: 'waiting',
    ...over,
})

const unit = (sources: DataSource[], over: Partial<UnitSources> = {}): UnitSources => ({
    unit: { code: 'NG', name: 'NICOLAS GOMES' },
    timezone: 'America/Manaus',
    dashboards: 3,
    lastFailure: null,
    sources,
    ...over,
})

const fresh = (over: Partial<SourceFreshness> = {}): SourceFreshness => ({
    fetchedAt: ago(11),
    cacheMin: 15,
    error: null,
    errorAt: null,
    ...over,
})

const only = (u: UnitSources) => u.sources[0]

describe('withFreshness (hora do registro de leituras da API, o mesmo do card do hub)', () => {
    it('última tentativa deu certo: saudável, com a hora e o tempo de cache', () => {
        const s = only(withFreshness(unit([source({})]), { lexflow: fresh() }))
        expect(s).toMatchObject({ status: 'healthy', syncedAt: ago(11), cacheMin: 15, failures: 0 })
    })

    it('ninguém abriu há horas, mas a última leitura deu certo: continua saudável (não atrasa por tempo)', () => {
        const s = only(withFreshness(unit([source({})]), { lexflow: fresh({ fetchedAt: ago(60 * 24) }) }))
        expect(s.status).toBe('healthy')
    })

    it('ainda não foi lida: aguardando leitura, não "aguardando sync"', () => {
        const s = only(withFreshness(unit([source({})]), { lexflow: fresh({ fetchedAt: null }) }))
        expect(s).toMatchObject({ status: 'on_open', syncedAt: null })
    })

    it('a tentativa mais recente falhou: com falha e vira a última falha da unidade', () => {
        const u = withFreshness(unit([source({})]), { lexflow: fresh({ error: 'TimeoutError', errorAt: ago(2) }) })
        expect(only(u)).toMatchObject({ status: 'failing', failures: 1, syncedAt: ago(11) })
        expect(u.lastFailure).toEqual({ at: ago(2), source: 'LexFlow', message: 'falha ao ler (TimeoutError)' })
    })

    it('desligada, a autorizar ou sem dashboards: o status do servidor fica (é configuração, não leitura)', () => {
        for (const status of ['disabled', 'pending', 'no_dashboards'] as const) {
            expect(only(withFreshness(unit([source({ status })]), { lexflow: fresh() })).status).toBe(status)
        }
    })

    it('sem resposta da API ou fonte fora da resposta: fica como veio do Supabase', () => {
        const original = unit([source({ id: 'ng', status: 'waiting' })])
        expect(withFreshness(original, null)).toEqual(original)
        expect(withFreshness(original, { lexflow: fresh() })).toEqual(original)
    })

    it('modal: a fonte sozinha segue a mesma regra da linha da lista', () => {
        const s = source({ status: 'waiting' })
        expect(sourceWithFreshness(s, fresh())).toEqual(only(withFreshness(unit([s]), { lexflow: fresh() })))
        expect(sourceWithFreshness(s, undefined)).toBe(s)
    })

    it('falha do Supabase mais recente que a do registro continua sendo a última falha', () => {
        const lastFailure = { at: ago(1), source: 'NG', message: 'tempo esgotado' }
        const u = withFreshness(unit([source({})], { lastFailure }), {
            lexflow: fresh({ error: 'TimeoutError', errorAt: ago(5) }),
        })
        expect(u.lastFailure).toEqual(lastFailure)
    })
})
