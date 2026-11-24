import { describe, expect, it } from 'vitest'
import { DOC_ENTRIES, GUIDE_ENTRIES, docFor, filterDocs, groupDocs, guideOrDoc, visibleDocs } from './docRegistry.ts'

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

describe('groupDocs e filterDocs', () => {
    const catalog = [
        { key: 'comercial-lexpre', area: 'Comercial' },
        { key: 'execucao', area: 'Jurídico' },
        { key: 'acordos', area: 'Jurídico' },
    ]
    const docs = DOC_ENTRIES.filter((d) => ['acordos', 'comercial-lexpre', 'execucao'].includes(d.slug))

    it('agrupa pela área do dashboard, na ordem do catálogo', () => {
        const groups = groupDocs(docs, catalog)
        expect(groups.map((g) => g.area)).toEqual(['Comercial', 'Jurídico'])
        expect(groups[1].docs.map((d) => d.slug)).toEqual(['execucao', 'acordos'])
    })

    it('dashboard fora do catálogo vai para Outros, no fim', () => {
        const groups = groupDocs(docs, [{ key: 'execucao', area: 'Jurídico' }])
        expect(groups.map((g) => g.area)).toEqual(['Jurídico', 'Outros'])
    })

    it('busca sem acento e filtra pela unidade; grupo vazio some', () => {
        const groups = groupDocs(docs, catalog)
        expect(filterDocs(groups, 'execucao', null).flatMap((g) => g.docs.map((d) => d.slug))).toEqual([
            'execucao',
            'acordos',
        ])
        expect(filterDocs(groups, 'juridico', null).map((g) => g.area)).toEqual(['Jurídico'])
        expect(filterDocs(groups, '', 'LA').flatMap((g) => g.docs.map((d) => d.slug))).toEqual([
            'comercial-lexpre',
            'execucao',
        ])
        expect(filterDocs(groups, 'nada disso', null)).toEqual([])
    })
})

describe('guias por unidade (trazidos da v1)', () => {
    it('cada unidade abre o guia dela, com os códigos de unidade do banco e do mock', () => {
        expect(docFor(DOC_ENTRIES, 'protocolo', 'NG')?.slug).toBe('protocolo-ng')
        expect(docFor(DOC_ENTRIES, 'protocolo', 'RJ')?.slug).toBe('protocolo-ng')
        expect(docFor(DOC_ENTRIES, 'protocolo', 'LA_RJ')?.slug).toBe('protocolo-ng')
        expect(docFor(DOC_ENTRIES, 'protocolo', 'LA')?.slug).toBe('protocolo-la')
        expect(docFor(DOC_ENTRIES, 'protocolo', 'LA_AM')?.slug).toBe('protocolo-la')
        expect(docFor(DOC_ENTRIES, 'replicas', 'LA')?.slug).toBe('replicas-la')
    })
})
