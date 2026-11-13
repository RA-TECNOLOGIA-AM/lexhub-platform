import { describe, expect, it } from 'vitest'
import type { DataSource, SourceDetail, SyncRun, UnitSources } from '../../../types/index.ts'
import {
    detailLabel,
    durationLabel,
    groupLabel,
    groupSources,
    lastFailureLabel,
    ownerLabel,
    pickUnit,
    rowsLabel,
    runResultLabel,
    statusOf,
    syncNote,
    unitLimitLabel,
    unitSub,
    whenLabel,
} from './sourcesView.ts'

const NOW = Date.parse('2026-11-10T12:00:00Z')
const ago = (min: number) => new Date(NOW - min * 60_000).toISOString()

const source = (over: Partial<DataSource>): DataSource => ({
    id: 's1',
    kind: 'database',
    group: 'product',
    name: 'LexPre',
    detail: '',
    managedBy: null,
    syncedAt: ago(4),
    rows: null,
    failures: 0,
    status: 'healthy',
    ...over,
})

const unit = (code: string, over: Partial<UnitSources> = {}): UnitSources => ({
    unit: { code, name: code },
    timezone: 'America/Manaus',
    dashboards: 0,
    lastFailure: null,
    sources: [],
    ...over,
})

describe('sourcesView', () => {
    it('monta o texto do cabeçalho com o intervalo do servidor', () => {
        expect(syncNote(5)).toContain('a cada 5 minutos')
    })

    it('resume linhas no padrão brasileiro', () => {
        expect(rowsLabel(18_000)).toBe('18 mil linhas')
        expect(rowsLabel(950)).toBe('950 linhas')
    })

    it('mostra quando sincronizou, com linhas ou falhas', () => {
        expect(whenLabel(source({ rows: 18_000 }), NOW)).toBe('há 4 min · 18 mil linhas')
        expect(whenLabel(source({ syncedAt: ago(180), failures: 2, status: 'late' }), NOW)).toBe(
            'há 3 h · 2 falhas seguidas',
        )
        expect(whenLabel(source({ syncedAt: ago(9) }), NOW)).toBe('há 9 min')
    })

    it('fonte sem sincronização: autorizar ou nunca sincronizada', () => {
        expect(whenLabel(source({ syncedAt: null, status: 'pending' }), NOW)).toBe('Ainda não autorizada')
        expect(whenLabel(source({ syncedAt: null }), NOW)).toBe('Nunca sincronizada')
    })

    it('textos da unidade', () => {
        const u = unit('NG', { sources: [source({}), source({ id: 's2' })] })
        expect(unitSub(u)).toBe('2 fontes · America/Manaus')
        expect(unitSub(unit('CP'))).toBe('0 fontes · America/Manaus')
        expect(lastFailureLabel(u)).toBe('Nenhuma nos últimos 7 dias')
        expect(
            lastFailureLabel(
                unit('NG', { lastFailure: { at: ago(1), source: 'LexPre', message: 'tempo esgotado (30 s)' } }),
            ),
        ).toBe('LexPre: tempo esgotado (30 s)')
        expect(unitLimitLabel({ used: 3, total: 5 })).toBe('3 de 5 unidades do plano')
        expect(unitLimitLabel(null)).toBeNull()
    })

    it('separa produtos contratados de fontes conectadas, nesta ordem, sem grupo vazio', () => {
        const db = source({ id: 'ng', group: 'connection' })
        const sections = groupSources([db, source({ id: 'lexpre' })])
        expect(sections.map((s) => s.title)).toEqual(['Produtos contratados', 'Fontes conectadas'])
        expect(sections[1].sources).toEqual([db])
        expect(groupSources([db]).map((s) => s.group)).toEqual(['connection'])
        expect(groupSources([])).toEqual([])
    })

    it('fonte de outra unidade diz quem gerencia', () => {
        expect(detailLabel(source({ detail: 'Postgres', managedBy: 'Nicolas Gomes' }))).toBe(
            'Postgres · gerenciada por Nicolas Gomes',
        )
        expect(detailLabel(source({ detail: 'Postgres' }))).toBe('Postgres')
    })

    it('fonte que ainda não sincronizou: aguardando', () => {
        expect(statusOf('waiting')).toEqual({ label: 'Aguardando sync', badge: 'badge neutral' })
        expect(whenLabel(source({ syncedAt: null, status: 'waiting' }), NOW)).toBe('Nunca sincronizada')
    })

    it('escolhe a unidade da URL ou a primeira', () => {
        const units = [unit('NG'), unit('LA_AM')]
        expect(pickUnit(units, 'LA_AM')?.unit.code).toBe('LA_AM')
        expect(pickUnit(units, 'XX')?.unit.code).toBe('NG')
        expect(pickUnit(units, null)?.unit.code).toBe('NG')
        expect(pickUnit([], null)).toBeUndefined()
    })
    it('modal: tipo e quem cuida da fonte, visto da unidade', () => {
        expect(groupLabel('product')).toBe('Produto contratado')
        expect(groupLabel('connection')).toBe('Fonte conectada')
        const detail = (owner: SourceDetail['owner']): SourceDetail => ({
            unit: { code: 'RJ', name: 'LARJ' },
            source: source({}),
            owner,
            dashboards: [],
            runs: [],
        })
        expect(ownerLabel(detail(null))).toBe('A organização (vem do contrato)')
        expect(ownerLabel(detail({ code: 'RJ', name: 'LARJ' }))).toBe('LARJ (esta unidade)')
        expect(ownerLabel(detail({ code: 'NG', name: 'Nicolas Gomes' }))).toBe('Nicolas Gomes (gerencia a conexão)')
    })

    it('modal: duração e resultado de cada sincronização', () => {
        const run = (over: Partial<SyncRun>): SyncRun => ({
            startedAt: ago(10),
            finishedAt: new Date(NOW - 10 * 60_000 + 42_000).toISOString(),
            ok: true,
            rows: 18_000,
            error: null,
            ...over,
        })
        expect(durationLabel(run({}))).toBe('42 s')
        expect(durationLabel(run({ finishedAt: new Date(NOW - 10 * 60_000 + 125_000).toISOString() }))).toBe(
            '2 min 5 s',
        )
        expect(durationLabel(run({ finishedAt: ago(7) }))).toBe('3 min')
        expect(durationLabel(run({ finishedAt: null, ok: null }))).toBe('rodando')
        expect(runResultLabel(run({}))).toBe('18 mil linhas')
        expect(runResultLabel(run({ rows: null }))).toBe('Concluída')
        expect(runResultLabel(run({ ok: false, rows: null, error: 'tempo esgotado (30 s)' }))).toBe(
            'tempo esgotado (30 s)',
        )
        expect(runResultLabel(run({ ok: false, rows: null }))).toBe('Falhou')
        expect(runResultLabel(run({ ok: null, finishedAt: null }))).toBe('Rodando')
    })
})
