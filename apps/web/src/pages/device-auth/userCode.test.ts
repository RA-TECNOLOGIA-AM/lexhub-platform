import { describe, expect, it } from 'vitest'
import { formatUserCode, normalizeUserCode } from './userCode.ts'

describe('normalizeUserCode', () => {
    it('aceita sem hífen, com espaços e minúsculas', () => {
        expect(normalizeUserCode('XB88GA8V')).toBe('XB88-GA8V')
        expect(normalizeUserCode(' xb88 ga8v ')).toBe('XB88-GA8V')
        expect(normalizeUserCode('XB88-GA8V')).toBe('XB88-GA8V')
    })

    it('recusa tamanho errado e letras que o código nunca usa (0, 1, I, O)', () => {
        expect(normalizeUserCode('XB88GA8')).toBeNull()
        expect(normalizeUserCode('XB88GA8V9')).toBeNull()
        expect(normalizeUserCode('XB80GA8V')).toBeNull()
        expect(normalizeUserCode('XBI8GA8V')).toBeNull()
    })
})

describe('formatUserCode', () => {
    it('põe o hífen sozinho enquanto digita', () => {
        expect(formatUserCode('xb8')).toBe('XB8')
        expect(formatUserCode('xb88')).toBe('XB88')
        expect(formatUserCode('xb88g')).toBe('XB88-G')
        expect(formatUserCode('XB88-GA8V')).toBe('XB88-GA8V')
    })

    it('ignora o que não é letra/número e corta no tamanho do código', () => {
        expect(formatUserCode('xb 88.ga8v99')).toBe('XB88-GA8V')
    })
})
