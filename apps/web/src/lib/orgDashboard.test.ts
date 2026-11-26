import { describe, expect, it } from 'vitest'
import { dashboardHref, unitLabel } from './orgDashboard.ts'

describe('orgDashboard', () => {
    it('dashboard da organização abre em /geral, ignorando a unidade escolhida', () => {
        expect(dashboardHref('lexgroup', 'NG', { key: 'estrategico-geral', scope: 'org' })).toBe(
            '/lexgroup/geral/dashboards/estrategico-geral',
        )
    })

    it('dashboard de unidade abre na unidade escolhida', () => {
        expect(dashboardHref('lexgroup', 'LA', { key: 'estrategico' })).toBe('/lexgroup/LA/dashboards/estrategico')
        expect(dashboardHref('lexgroup', 'RJ', { key: 'estrategico', scope: 'unit' })).toBe(
            '/lexgroup/RJ/dashboards/estrategico',
        )
    })

    it("'geral' no cabeçalho vira 'Todas as unidades'", () => {
        expect(unitLabel('geral', 'geral')).toBe('Todas as unidades')
        expect(unitLabel('NG', 'Nicolas Gomes')).toBe('Nicolas Gomes')
    })
})
