// Módulo: os campos de um relatório de exportação, sem React (testado em exportFields.test.ts).
// Cada dashboard declara os seus (cópia da lista do servidor, como na v1); a janela só desenha.

export type ExportField = { slug: string; label: string } // slug = o nome que a API espera em ?campos=
export type ExportGroup = { group: string; fields: ExportField[] }
import type { ExportRequest } from '../types/index.ts'
export type ExportFormat = ExportRequest['format'] // um lugar só para 'csv' | 'xlsx'

// Todos os slugs, na ordem dos grupos.
export const allSlugs = (groups: ExportGroup[]): string[] => groups.flatMap((g) => g.fields.map((f) => f.slug))

// Marca ou desmarca um campo.
export const toggleSlug = (selected: string[], slug: string): string[] =>
    selected.includes(slug) ? selected.filter((s) => s !== slug) : [...selected, slug]

// Os escolhidos na ordem dos grupos (não na ordem dos cliques): é a ordem das colunas no arquivo.
export const orderedSelection = (groups: ExportGroup[], selected: string[]): string[] =>
    allSlugs(groups).filter((slug) => selected.includes(slug))

// '29 de 29 campos selecionados'
export const selectionLabel = (selected: number, total: number): string =>
    `${selected} de ${total} ${total === 1 ? 'campo selecionado' : 'campos selecionados'}`
