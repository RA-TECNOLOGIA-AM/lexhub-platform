import { describe, expect, it } from 'vitest'
import { DOC_ENTRIES, docFor, visibleDocs } from './docRegistry.ts'

describe('visibleDocs', () => {
    it('só as documentações dos dashboards que a pessoa abre', () => {
        const slugs = visibleDocs(DOC_ENTRIES, [{ key: 'protocolo-lexpre', units: ['NG'] }]).map((d) => d.slug)
        expect(slugs).toEqual(['protocolo-lexpre'])
    })

    it('guia de uma unidade só aparece se o dashboard estiver liberado nela', () => {
        const slugs = visibleDocs(DOC_ENTRIES, [{ key: 'recursal', units: ['NG'] }]).map((d) => d.slug)
        expect(slugs).toEqual(['recursal-ng'])
    })

    it('nenhum dashboard: nenhuma documentação', () => {
        expect(visibleDocs(DOC_ENTRIES, [])).toEqual([])
    })
})

describe('docFor', () => {
    it('escolhe o guia da unidade; sem variação por unidade, o geral', () => {
        expect(docFor(DOC_ENTRIES, 'recursal', 'LA')?.slug).toBe('recursal-la')
        expect(docFor(DOC_ENTRIES, 'recursal', 'NG')?.slug).toBe('recursal-ng')
        expect(docFor(DOC_ENTRIES, 'protocolo-lexpre', 'RJ')?.slug).toBe('protocolo-lexpre')
        expect(docFor(DOC_ENTRIES, 'nps', 'NG')).toBeNull()
    })

    it('todo slug é único', () => {
        const slugs = DOC_ENTRIES.map((d) => d.slug)
        expect(new Set(slugs).size).toBe(slugs.length)
    })
})
