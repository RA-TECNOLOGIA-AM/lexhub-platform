import { describe, expect, it } from 'vitest'
import { searchDashboards } from './dashboardSearch.ts'

const LIST = [
    { title: 'Protocolo', area: 'Operação jurídica', desc: 'Protocolados, rejeitados e devoluções.' },
    { title: 'Pré-protocolo', area: 'Operação jurídica', desc: 'Casos antes do protocolo.' },
    { title: 'Estratégico', area: 'Gestão', desc: 'Visão geral das unidades.' },
    { title: 'Comissão', area: 'Comercial', desc: 'Comissão por atendente e por rubrica.' },
]
const titles = (list: { title: string }[]) => list.map((d) => d.title)

describe('searchDashboards', () => {
    it('procura no título, sem acento e sem maiúsculas', () => {
        expect(titles(searchDashboards(LIST, 'ESTRATEGICO'))).toEqual(['Estratégico'])
    })

    it('procura na área e na descrição', () => {
        expect(titles(searchDashboards(LIST, 'gestao'))).toEqual(['Estratégico'])
        expect(titles(searchDashboards(LIST, 'rubrica'))).toEqual(['Comissão'])
    })

    it('devolve todos os que combinam, na ordem da lista', () => {
        expect(titles(searchDashboards(LIST, 'protocolo'))).toEqual(['Protocolo', 'Pré-protocolo'])
    })

    it('busca vazia devolve tudo; sem resultado devolve lista vazia', () => {
        expect(searchDashboards(LIST, '')).toHaveLength(4)
        expect(searchDashboards(LIST, 'xyz')).toEqual([])
    })
})
