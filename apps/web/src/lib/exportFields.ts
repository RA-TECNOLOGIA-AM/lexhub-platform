// Módulo: os campos de um relatório de exportação, sem React (testado em exportFields.test.ts).
// Cada dashboard declara os seus (cópia da lista do servidor, como na v1); a janela só desenha.

export type ExportField = { slug: string; label: string } // slug = o nome que a API espera em ?campos=
// block: o bloco do grupo num relatório com partes (ex.: 'Condenação' e 'Acordos' no "Os dois juntos" do Execução
// Estratégico); cada bloco tem o seu "Selecionar todos" na janela, como na v1.
export type ExportGroup = { group: string; fields: ExportField[]; block?: string }
// Uma escolha da exportação além dos campos (ex.: o recorte entrada/saida/total da Execução, ?criterio=).
// A primeira opção é a padrão, como no servidor (ExportOption).
// note: a explicação da escolha, embaixo dela na janela (ex.: o que o "Relatório personalizado" ignora).
export type ExportOptionDef = {
    key: string
    label: string
    choices: { value: string; label: string; note?: string }[]
}
// Um relatório do dashboard: key null = o principal; outra = ?relatorio=<key> (ex.: as Atividades dos Acordos).
export type ExportReport = { key: string | null; title: string; groups: ExportGroup[]; options?: ExportOptionDef[] }

// As escolhas padrão de um relatório (a primeira de cada opção).
export const defaultOptions = (report: ExportReport): Record<string, string> =>
    Object.fromEntries((report.options ?? []).map((o) => [o.key, o.choices[0]?.value ?? '']))
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
