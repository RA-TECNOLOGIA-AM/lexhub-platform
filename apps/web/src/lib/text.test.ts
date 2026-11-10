import { describe, expect, it } from 'vitest'
import { matchesText, normalizeText } from './text.ts'

describe('text', () => {
    it('tira acento e maiúsculas', () => {
        expect(normalizeText('Pré-Protocolo')).toBe('pre-protocolo')
        expect(normalizeText('GESTÃO')).toBe('gestao')
    })

    it('acha sem se importar com acento ou maiúsculas, dos dois lados', () => {
        expect(matchesText('Gestão', 'gestao')).toBe(true)
        expect(matchesText('Comissao', 'Comissão')).toBe(true)
        expect(matchesText('Organização de documentos', 'DOC')).toBe(true)
        expect(matchesText('Protocolo', 'pendência')).toBe(false)
    })

    it('busca vazia ou só espaços combina com tudo; espaços nas pontas são ignorados', () => {
        expect(matchesText('Qualquer coisa', '')).toBe(true)
        expect(matchesText('Qualquer coisa', '   ')).toBe(true)
        expect(matchesText('Protocolo', '  proto ')).toBe(true)
    })
})
