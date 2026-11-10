import { describe, expect, it } from 'vitest'
import { DataError } from '../../services/errors.ts'
import type { DashboardCatalog } from '../../types/index.ts'
import { baseMeta } from './baseView.ts'

const CATALOG: DashboardCatalog = {
    upcoming: [],
    available: [
        {
            key: 'nps',
            title: 'NPS',
            area: 'Comercial',
            desc: 'Satisfação dos clientes.',
            units: ['NG', 'LA_AM'],
            source: 'LexPre',
            synced_at: '2026-11-10T12:00:00Z',
            max_delay_min: 60,
            can_export: true,
            can_see_commission: false,
        },
    ],
}

// Roda a função e devolve o erro que ela lançou (ou undefined).
function errorOf(run: () => unknown): unknown {
    try {
        run()
    } catch (error) {
        return error
    }
}

describe('baseMeta', () => {
    it('monta o meta com a fonte e a atualização do catálogo', () => {
        expect(baseMeta(CATALOG, 'nps', 'NG')).toEqual({
            unit: 'NG',
            from: '',
            to: '',
            source: 'LexPre',
            synced_at: '2026-11-10T12:00:00Z',
            timezone: '',
        })
    })

    it('unidade não liberada: 403', () => {
        const error = errorOf(() => baseMeta(CATALOG, 'nps', 'LA_RJ'))
        expect(error).toBeInstanceOf(DataError)
        expect((error as DataError).status).toBe(403)
    })

    it('dashboard que não existe: o mesmo 403 (não revela o que existe)', () => {
        expect((errorOf(() => baseMeta(CATALOG, 'xyz', 'NG')) as DataError).status).toBe(403)
    })
})
