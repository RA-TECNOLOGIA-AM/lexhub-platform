import { describe, expect, it } from 'vitest'
import { allSlugs, orderedSelection, selectionLabel, toggleSlug, type ExportGroup } from './exportFields.ts'

const GROUPS: ExportGroup[] = [
    {
        group: 'Identificação',
        fields: [
            { slug: 'id', label: 'ID' },
            { slug: 'nome', label: 'Nome' },
        ],
    },
    { group: 'Datas', fields: [{ slug: 'entrada', label: 'Entrada' }] },
]

describe('exportFields', () => {
    it('lista todos os campos na ordem dos grupos', () => {
        expect(allSlugs(GROUPS)).toEqual(['id', 'nome', 'entrada'])
    })

    it('marca e desmarca um campo', () => {
        expect(toggleSlug(['id'], 'nome')).toEqual(['id', 'nome'])
        expect(toggleSlug(['id', 'nome'], 'id')).toEqual(['nome'])
    })

    it('colunas na ordem dos grupos, não na dos cliques', () => {
        expect(orderedSelection(GROUPS, ['entrada', 'id'])).toEqual(['id', 'entrada'])
    })

    it('texto da contagem', () => {
        expect(selectionLabel(29, 29)).toBe('29 de 29 campos selecionados')
        expect(selectionLabel(0, 1)).toBe('0 de 1 campo selecionado')
    })
})
