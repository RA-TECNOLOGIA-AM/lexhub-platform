import { describe, expect, it } from 'vitest'
import { countFilters, toggleFilter } from './filters.ts'

describe('filters', () => {
    it('conta todos os valores escolhidos', () => {
        expect(countFilters({})).toBe(0)
        expect(countFilters({ materia: ['ANP', 'MORA'], uf: ['AM'] })).toBe(3)
    })

    it('marca e desmarca um valor', () => {
        const one = toggleFilter({}, 'materia', 'ANP')
        expect(one).toEqual({ materia: ['ANP'] })
        expect(toggleFilter(one, 'materia', 'MORA')).toEqual({ materia: ['ANP', 'MORA'] })
    })

    it('filtro sem nenhum valor sai do objeto', () => {
        expect(toggleFilter({ materia: ['ANP'], uf: ['AM'] }, 'materia', 'ANP')).toEqual({ uf: ['AM'] })
    })

    it('não altera o objeto original', () => {
        const original = { materia: ['ANP'] }
        toggleFilter(original, 'materia', 'MORA')
        expect(original).toEqual({ materia: ['ANP'] })
    })
})
