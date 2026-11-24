import { describe, expect, it } from 'vitest'
import {
    buildSemanticColors,
    contrastWithWhite,
    DEFAULT_THEME,
    isValidAccentId,
    isValidThemeId,
    resolveAccentHex,
    THEME_ACCENTS,
    THEME_PRESETS,
    themePreview,
} from './themeEngine.ts'

// Contraste WCAG entre duas cores hex (para conferir que todo tema fica legível).
function luminance(hex: string): number {
    const channel = (i: number) => {
        const x = parseInt(hex.slice(1 + i, 3 + i), 16) / 255
        return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4
    }
    return 0.2126 * channel(0) + 0.7152 * channel(2) + 0.0722 * channel(4)
}
function contrast(a: string, b: string): number {
    const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
    return (hi + 0.05) / (lo + 0.05)
}

const engineThemes = THEME_PRESETS.filter((t) => !t.builtIn)

describe('THEME_PRESETS (mesma lista do LexFlow)', () => {
    it('15 claros e 27 escuros, ids únicos', () => {
        expect(THEME_PRESETS.filter((t) => t.mode === 'light')).toHaveLength(15)
        expect(THEME_PRESETS.filter((t) => t.mode === 'dark')).toHaveLength(27)
        expect(new Set(THEME_PRESETS.map((t) => t.id)).size).toBe(THEME_PRESETS.length)
    })

    it('os padrões são os do LexHub (sem motor), com o laranja/âmbar da marca', () => {
        const light = THEME_PRESETS.find((t) => t.id === DEFAULT_THEME.light)
        const dark = THEME_PRESETS.find((t) => t.id === DEFAULT_THEME.dark)
        expect(light).toMatchObject({ name: 'Claro Padrão', mode: 'light', builtIn: true, accent: '#b35500' })
        expect(dark).toMatchObject({ name: 'Escuro Padrão', mode: 'dark', builtIn: true, accent: '#f5a04a' })
        expect(engineThemes).toHaveLength(40)
    })

    it('o destaque de todo tema do motor passa 4.5:1 com texto branco', () => {
        for (const t of engineThemes) expect(contrastWithWhite(t.accent), t.id).toBeGreaterThanOrEqual(4.5)
    })

    it('todo tema do motor tem texto legível sobre o fundo, o cartão e a moldura', () => {
        for (const t of engineThemes) {
            const c = buildSemanticColors(t)
            expect(contrast(c.text.primary, c.background.primary), t.id).toBeGreaterThanOrEqual(4.5)
            expect(contrast(c.text.primary, c.surface.secondary), t.id).toBeGreaterThanOrEqual(4.5)
            expect(contrast(c.text.secondary, c.background.secondary), t.id).toBeGreaterThanOrEqual(4.5)
        }
    })

    it('Dracula nasce do fundo #282a36', () => {
        const dracula = THEME_PRESETS.find((t) => t.id === 'dark-dracula')!
        expect(buildSemanticColors(dracula).background.primary).toMatch(/^#2[0-9a-f]2[0-9a-f]3[0-9a-f]$/)
    })
})

describe('THEME_ACCENTS', () => {
    it('Do tema + 14 cores, todas legíveis com texto branco', () => {
        expect(THEME_ACCENTS[0]).toEqual({ id: 'tema', name: 'Do tema', hex: null })
        expect(THEME_ACCENTS).toHaveLength(15)
        for (const a of THEME_ACCENTS) if (a.hex) expect(contrastWithWhite(a.hex), a.id).toBeGreaterThanOrEqual(4.5)
    })
})

describe('resolveAccentHex', () => {
    it('"Do tema" (ou nada) usa a cor do tema', () => {
        expect(resolveAccentHex('tema', '#abcdef')).toBe('#abcdef')
        expect(resolveAccentHex(null, '#abcdef')).toBe('#abcdef')
    })
    it('cor pronta e cor livre', () => {
        expect(resolveAccentHex('azul', '#abcdef')).toBe('#2563eb')
        expect(resolveAccentHex('#E11D48', '#abcdef')).toBe('#e11d48')
    })
    it('id desconhecido cai na cor do tema', () => {
        expect(resolveAccentHex('xyz', '#abcdef')).toBe('#abcdef')
    })
})

describe('validação de ids', () => {
    it('tema: existe e é do modo pedido', () => {
        expect(isValidThemeId('dark-dracula', 'dark')).toBe(true)
        expect(isValidThemeId('dark-dracula', 'light')).toBe(false)
        expect(isValidThemeId('nao-existe', 'dark')).toBe(false)
        expect(isValidThemeId(null, 'dark')).toBe(false)
    })
    it('destaque: id de cor pronta ou hex de 6 dígitos', () => {
        expect(isValidAccentId('tema')).toBe(true)
        expect(isValidAccentId('azul')).toBe(true)
        expect(isValidAccentId('#2563eb')).toBe(true)
        expect(isValidAccentId('#12')).toBe(false)
        expect(isValidAccentId('roxo-neon')).toBe(false)
    })
})

describe('themePreview', () => {
    it('padrões com as cores atuais do LexHub', () => {
        expect(themePreview('light-default')).toEqual({
            bg: '#f4f5f7',
            sidebar: '#11151a',
            sideText: '#c9ced6',
            card: '#ffffff',
            text: '#15181d',
            border: '#e3e6eb',
            accent: '#b35500',
        })
        expect(themePreview('dark-default').bg).toBe('#14110e')
    })
    it('tema do motor sai das cores calculadas; id desconhecido = Claro Padrão', () => {
        const nord = themePreview('dark-nord')
        expect(nord.accent).toBe(THEME_PRESETS.find((t) => t.id === 'dark-nord')!.accent)
        expect(themePreview('nao-existe')).toEqual(themePreview('light-default'))
    })
})
