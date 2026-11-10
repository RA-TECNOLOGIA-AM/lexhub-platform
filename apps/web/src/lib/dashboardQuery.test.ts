import { describe, expect, it } from 'vitest'
import { paramsFromQuery, queryFromParams } from './dashboardQuery.ts'

describe('dashboardQuery', () => {
    it('lê período e filtros repetidos da URL', () => {
        const params = new URLSearchParams('from=2026-10-01&to=2026-10-31&materia=ANP&materia=MORA&uf=AM')
        expect(queryFromParams(params)).toEqual({
            from: '2026-10-01',
            to: '2026-10-31',
            filters: { materia: ['ANP', 'MORA'], uf: ['AM'] },
        })
    })

    it('período incompleto ou invertido fica de fora (vale o padrão do servidor)', () => {
        expect(queryFromParams(new URLSearchParams('from=2026-10-01'))).toEqual({ filters: {} })
        expect(queryFromParams(new URLSearchParams('from=2026-10-31&to=2026-10-01'))).toEqual({ filters: {} })
    })

    it('ignora parâmetros desconhecidos e valores vazios', () => {
        expect(queryFromParams(new URLSearchParams('busca=x&materia=&uf=RJ'))).toEqual({ filters: { uf: ['RJ'] } })
    })

    it('ida e volta: o que sai da URL volta igual', () => {
        const text = 'from=2026-10-01&to=2026-10-31&materia=ANP&materia=MORA&uf=AM'
        expect(paramsFromQuery(queryFromParams(new URLSearchParams(text))).toString()).toBe(text)
    })
})
