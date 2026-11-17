import { describe, expect, it } from 'vitest'
import type { DataSource, ProductOffice } from '../../../types/index.ts'
import { CONNECTORS, connectorBlock, officeSub, sortOffices } from './connectSource.ts'

const office = (ref: string, name: string, linked = false): ProductOffice => ({
    ref,
    name,
    activity: 1234,
    linkedTo: linked ? { org: 'LexGroup', unit: 'NG', unitName: 'Nicolas Gomes' } : null,
})

const lexpre = { id: 'lexpre' } as DataSource

describe('connectSource', () => {
    it('só LexPre e LexFlow estão prontos nesta versão', () => {
        expect(CONNECTORS.filter((c) => c.ready).map((c) => c.key)).toEqual(['lexpre', 'lexflow'])
    })

    it('bloqueia tipo em breve e produto que a unidade já tem', () => {
        expect(connectorBlock('postgres', false, [])).toBe('Em breve')
        expect(connectorBlock('lexpre', true, [lexpre])).toBe('Já ligado a esta unidade')
        expect(connectorBlock('lexflow', true, [lexpre])).toBeNull()
    })

    it('escritórios livres primeiro, por nome; ligados no fim', () => {
        const sorted = sortOffices([office('1', 'Nicolas Gomes', true), office('5', 'Belém'), office('4', 'Amazonas')])
        expect(sorted.map((o) => o.ref)).toEqual(['4', '5', '1'])
    })

    it('a linha de baixo mostra a atividade ou onde já está ligado', () => {
        expect(officeSub(office('4', 'A'), 'processos')).toBe('1.234 processos')
        expect(officeSub(office('1', 'B', true), 'processos')).toBe('Ligado à unidade NG (LexGroup)')
    })
})
