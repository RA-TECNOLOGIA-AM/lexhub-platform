import { describe, expect, it } from 'vitest'
import { normalizeCode, suggestCode, timezoneLabel, validateUnit } from './unitForm.ts'

describe('unitForm', () => {
    it('sugere o código pelo nome', () => {
        expect(suggestCode('Luis Albert RJ')).toBe('LARJ')
        expect(suggestCode('Nicolas Gomes')).toBe('NG')
        expect(suggestCode('Escritório Master')).toBe('EM')
        expect(suggestCode('Sede')).toBe('SEDE')
        expect(suggestCode('  ')).toBe('')
    })

    it('o campo código só aceita maiúsculas, números e _ (até 16)', () => {
        expect(normalizeCode('la-rj ção')).toBe('LARJCAO')
        expect(normalizeCode('a'.repeat(20))).toBe('A'.repeat(16))
    })

    it('rótulo do fuso', () => {
        expect(timezoneLabel('America/Manaus')).toBe('Manaus (AM) · UTC−4')
        expect(timezoneLabel('Europe/Lisbon')).toBe('Europe/Lisbon')
    })

    it('valida antes de enviar', () => {
        const ok = { code: 'SP', name: 'São Paulo', timezone: 'America/Sao_Paulo' }
        expect(validateUnit(ok, 'create', ['NG'])).toBeNull()
        expect(validateUnit({ ...ok, name: ' ' }, 'create', [])).toBe('Informe o nome da unidade.')
        expect(validateUnit({ ...ok, code: 'X' }, 'create', [])).toMatch(/^Código inválido/)
        expect(validateUnit(ok, 'create', ['SP'])).toBe('Já existe uma unidade com o código SP.')
        expect(validateUnit({ ...ok, timezone: 'Marte/Olympus' }, 'create', [])).toMatch(/^Fuso inválido/)
        // Na edição o código não conta (ele não muda)
        expect(validateUnit({ ...ok, code: '' }, 'edit', ['SP'])).toBeNull()
    })
})
