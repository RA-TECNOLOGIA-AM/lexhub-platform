import { describe, expect, it } from 'vitest'
import type { DashboardCatalog, DashboardSummary } from '../types/index.ts'
import { isDisabled, withEnabled } from './dashboardSwitch.ts'

const card = (over: Partial<DashboardSummary> = {}): DashboardSummary => ({
    key: 'comercial',
    title: 'Comercial',
    area: 'Comercial',
    desc: '',
    units: ['NG', 'RJ'],
    source: 'NG',
    synced_at: null,
    max_delay_min: 60,
    can_export: true,
    can_see_commission: true,
    ...over,
})

describe('isDisabled', () => {
    it('numa unidade: só ela conta', () => {
        const d = card({ disabled_units: ['RJ'] })
        expect(isDisabled(d, 'RJ')).toBe(true)
        expect(isDisabled(d, 'NG')).toBe(false)
    })

    it('em todas as unidades: só quando desligado em todas', () => {
        expect(isDisabled(card({ disabled_units: ['RJ'] }), null)).toBe(false)
        expect(isDisabled(card({ disabled_units: ['NG', 'RJ'] }), null)).toBe(true)
        expect(isDisabled(card(), null)).toBe(false) // sem o campo (quem não é Dev)
    })
})

describe('withEnabled', () => {
    const catalog: DashboardCatalog = { available: [card(), card({ key: 'nps' })], upcoming: [] }

    it('desliga e religa só o dashboard e a unidade pedidos', () => {
        const off = withEnabled(catalog, 'comercial', 'RJ', false)
        expect(off.available[0].disabled_units).toEqual(['RJ'])
        expect(off.available[1].disabled_units).toBeUndefined()

        const on = withEnabled(off, 'comercial', 'RJ', true)
        expect(on.available[0].disabled_units).toEqual([])
    })

    it('desligar de novo não repete a unidade', () => {
        const twice = withEnabled(withEnabled(catalog, 'comercial', 'RJ', false), 'comercial', 'RJ', false)
        expect(twice.available[0].disabled_units).toEqual(['RJ'])
    })
})
