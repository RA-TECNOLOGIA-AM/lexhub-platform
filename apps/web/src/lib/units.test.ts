import { describe, expect, it } from 'vitest'
import { unitName } from './units.ts'

const UNITS = [{ code: 'NG', name: 'Nicolas Gomes' }]

describe('unitName', () => {
    it('usa o nome da unidade da pessoa', () => {
        expect(unitName('NG', UNITS)).toBe('Nicolas Gomes')
    })

    it('unidade que não é física (Consolidado) ou desconhecida mostra o código', () => {
        expect(unitName('Consolidado', UNITS)).toBe('Consolidado')
        expect(unitName('LA_RJ', [])).toBe('LA_RJ')
    })
})
