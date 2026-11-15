import { describe, expect, it } from 'vitest'
import { clearFilter, countFilters, filterChips, pickerLabel, toggleFilter, type FilterField } from './filters.ts'

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

describe('filterChips', () => {
    const fields: FilterField[] = [
        {
            key: 'materia',
            label: 'Matéria',
            options: [
                { value: 'ANP', label: 'ANP' },
                { value: 'MORA', label: 'Mora' },
            ],
        },
    ]

    it('uma etiqueta por valor, com o nome da opção', () => {
        expect(filterChips(fields, { materia: ['MORA', 'ANP'] }).map((c) => c.label)).toEqual([
            'Matéria: Mora',
            'Matéria: ANP',
        ])
    })

    it('sem filtros: nenhuma etiqueta', () => {
        expect(filterChips(fields, {})).toEqual([])
    })
})

describe('pickerLabel e clearFilter', () => {
    const field: FilterField = {
        key: 'uf',
        label: 'UF',
        options: [
            { value: 'AM', label: 'AM' },
            { value: 'PA', label: 'Pará' },
        ],
    }

    it('nome, opção escolhida ou "+n"', () => {
        expect(pickerLabel(field, [])).toBe('UF')
        expect(pickerLabel(field, ['PA'])).toBe('Pará')
        expect(pickerLabel(field, ['AM', 'PA'])).toBe('AM +1')
    })

    it('chip traz o valor sozinho para a faixa', () => {
        expect(filterChips([field], { uf: ['PA'] })[0]).toMatchObject({ text: 'Pará', label: 'UF: Pará' })
    })

    it('tira o filtro inteiro', () => {
        expect(clearFilter({ uf: ['AM'], materia: ['ANP'] }, 'uf')).toEqual({ materia: ['ANP'] })
    })
})
