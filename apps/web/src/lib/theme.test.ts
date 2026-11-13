import { describe, expect, it } from 'vitest'
import { oppositeTheme, resolveTheme, storedTheme, storeTheme, THEME_KEY } from './theme.ts'

function memory(initial: Record<string, string> = {}) {
    const data = { ...initial }
    return {
        data,
        getItem: (k: string) => data[k] ?? null,
        setItem: (k: string, v: string) => {
            data[k] = v
        },
    }
}

describe('storedTheme', () => {
    it('lê a escolha guardada', () => {
        expect(storedTheme(memory({ [THEME_KEY]: 'dark' }))).toBe('dark')
        expect(storedTheme(memory({ [THEME_KEY]: 'light' }))).toBe('light')
    })

    it('ignora valor estranho, ausência e storage que falha', () => {
        expect(storedTheme(memory({ [THEME_KEY]: 'roxo' }))).toBeNull()
        expect(storedTheme(memory())).toBeNull()
        expect(storedTheme(null)).toBeNull()
        const broken = {
            getItem: () => {
                throw new Error('bloqueado')
            },
        }
        expect(storedTheme(broken)).toBeNull()
    })
})

describe('storeTheme', () => {
    it('guarda a escolha e não quebra sem storage', () => {
        const storage = memory()
        storeTheme('dark', storage)
        expect(storage.data[THEME_KEY]).toBe('dark')
        expect(() => storeTheme('light', null)).not.toThrow()
    })
})

describe('resolveTheme', () => {
    it('a escolha da pessoa manda sobre o sistema', () => {
        expect(resolveTheme('light', true)).toBe('light')
        expect(resolveTheme('dark', false)).toBe('dark')
    })

    it('sem escolha, segue o sistema', () => {
        expect(resolveTheme(null, true)).toBe('dark')
        expect(resolveTheme(null, false)).toBe('light')
    })
})

describe('oppositeTheme', () => {
    it('alterna entre claro e escuro', () => {
        expect(oppositeTheme('light')).toBe('dark')
        expect(oppositeTheme('dark')).toBe('light')
    })
})
