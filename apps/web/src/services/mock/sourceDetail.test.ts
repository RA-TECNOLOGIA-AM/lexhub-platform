import { describe, expect, it } from 'vitest'
import { catalog } from './catalog.ts'
import { sources } from './sources.ts'
import { sourceDetailFor } from './sourceDetail.ts'

describe('sourceDetailFor (mock de api.source_detail)', () => {
    it('banco NG visto do LARJ: a dona é Nicolas Gomes', () => {
        const d = sourceDetailFor(sources, catalog, 'LA_RJ', 'ng')!
        expect(d.owner?.code).toBe('NG')
        expect(d.source.managedBy).toBe(d.owner?.name)
    })

    it('dashboards: só os da fonte que estão nesta unidade', () => {
        const d = sourceDetailFor(sources, catalog, 'NG', 'ng')!
        const ng = catalog.available.filter((x) => x.source === 'NG' && x.units.includes('NG'))
        expect(ng.length).toBeGreaterThan(0)
        expect(d.dashboards.map((x) => x.key)).toEqual(ng.map((x) => x.key))
        // No mock, os dashboards do NG só estão na unidade NG
        expect(sourceDetailFor(sources, catalog, 'LA_RJ', 'ng')!.dashboards).toEqual([])
    })

    it('produto contratado não tem dona; fonte aguardando não tem sincronizações', () => {
        expect(sourceDetailFor(sources, catalog, 'NG', 'lexpre')!.owner).toBeNull()
        expect(sourceDetailFor(sources, catalog, 'LA_AM', 'sheets_financeiro_la')!.runs).toEqual([])
    })

    it('fonte atrasada traz as falhas no topo', () => {
        const runs = sourceDetailFor(sources, catalog, 'NG', 'sheets_protocolo_passado_ng')!.runs
        expect(runs[0].ok).toBe(false)
        expect(runs.at(-1)?.ok).toBe(true)
    })

    it('unidade que não usa a fonte: null (o mock responde 409, como a API)', () => {
        expect(sourceDetailFor(sources, catalog, 'LA_AM', 'ng')).toBeNull()
        expect(sourceDetailFor(sources, catalog, 'XX', 'ng')).toBeNull()
    })
})
