import { describe, expect, it } from 'vitest'
import { DOC_ENTRIES, GUIDE_ENTRIES, docFor, guideOrDoc, visibleDocs } from './docRegistry.ts'

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
        expect(docFor(DOC_ENTRIES, 'julgados-acordaos', 'RJ')?.slug).toBe('julgados-acordaos')
        expect(docFor(DOC_ENTRIES, 'nps', 'NG')).toBeNull()
    })

    it('todo slug é único (guias de uso e de dashboards juntos)', () => {
        const slugs = [...GUIDE_ENTRIES, ...DOC_ENTRIES].map((d) => d.slug)
        expect(new Set(slugs).size).toBe(slugs.length)
    })
})

describe('guideOrDoc', () => {
    it('acha guia de uso e guia de dashboard; slug desconhecido = null', () => {
        expect(guideOrDoc('guia-do-usuario')?.title).toBe('Como usar o LexHub')
        expect(guideOrDoc('acordos')?.title).toBe('Execução Acordos')
        expect(guideOrDoc('nao-existe')).toBeNull()
    })
})
