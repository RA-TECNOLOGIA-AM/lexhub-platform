// Módulo: o catálogo de temas e o motor que calcula as cores de cada um (sem React, testado em themeEngine.test.ts).
// Portado do LexFlow (LexFlowNextBeta/src/design-system/theme-engine.ts + theme.ts), com os mesmos ids,
// nomes e cores-base, para os dois produtos terem a mesma galeria.
// - Cada tema nasce de duas cores (fundo e destaque). O motor calcula em OKLCH as camadas neutras
//   (fundo, moldura, cartões, bordas, texto), com limites de luminosidade e contraste: todo tema fica legível.
// - Exceção do LexHub: "Claro Padrão" e "Escuro Padrão" (builtIn) não passam pelo motor. São o visual
//   do tokens.css (claro atual e Carvão quente), com o laranja/âmbar da marca como destaque.
// - Quem traduz estas cores para as variáveis do LexHub é o lib/appearance.ts.

import type { ThemeMode } from '../types/index.ts'

export type SemanticColors = {
    background: { primary: string; secondary: string; tertiary: string; elevated: string }
    text: { primary: string; secondary: string; tertiary: string; disabled: string }
    border: { primary: string; secondary: string }
    surface: { primary: string; secondary: string; tertiary: string; elevated: string }
}

export type ThemePreset = {
    id: string
    name: string
    mode: ThemeMode
    hue: number // matiz do neutro (graus OKLCH)
    chroma: number // croma do neutro: 0 = cinza puro
    base: number // luminosidade da camada de conteúdo (0..1)
    contrast: number // distância entre camadas e força do texto; 1 = normal
    accent: string // destaque próprio do tema (usado em "Do tema"), hex minúsculo
    builtIn: boolean // true = padrão do LexHub (tokens.css), fora do motor
}

export type ThemePreview = {
    bg: string
    sidebar: string
    sideText: string // texto sobre a barra lateral (no Claro Padrão a barra é escura)
    card: string
    text: string
    border: string
    accent: string
}

// ─── OKLCH ⇄ sRGB ────────────────────────────────────────────────────────────

function toGamma(x: number): number {
    const v = x <= 0.0031308 ? 12.92 * x : 1.055 * Math.pow(x, 1 / 2.4) - 0.055
    return Math.min(1, Math.max(0, v))
}

// OKLCH (L 0..1, C ~0..0.37, H em graus) → hex sRGB.
export function oklchToHex(l: number, c: number, h: number): string {
    const hr = (h * Math.PI) / 180
    const a = c * Math.cos(hr)
    const b = c * Math.sin(hr)

    const l_ = l + 0.3963377774 * a + 0.2158037573 * b
    const m_ = l - 0.1055613458 * a - 0.0638541728 * b
    const s_ = l - 0.0894841775 * a - 1.291485548 * b

    const L = l_ ** 3
    const M = m_ ** 3
    const S = s_ ** 3

    const r = 4.0767416621 * L - 3.3077115913 * M + 0.2309699292 * S
    const g = -1.2684380046 * L + 2.6097574011 * M - 0.3413193965 * S
    const bl = -0.0041960863 * L - 0.7034186147 * M + 1.707614701 * S

    const hex = (v: number) =>
        Math.round(toGamma(v) * 255)
            .toString(16)
            .padStart(2, '0')
    return `#${hex(r)}${hex(g)}${hex(bl)}`
}

// hex sRGB → OKLCH.
export function hexToOklch(hex: string): { l: number; c: number; h: number } {
    const v = hex.replace('#', '')
    const full =
        v.length === 3
            ? v
                  .split('')
                  .map((ch) => ch + ch)
                  .join('')
            : v
    const lin = (i: number) => {
        const x = parseInt(full.slice(i, i + 2), 16) / 255
        return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4
    }
    const r = lin(0)
    const g = lin(2)
    const b = lin(4)
    const l_ = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    const m_ = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    const s_ = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    const L = 0.2104542553 * l_ + 0.793617785 * m_ - 0.0040720468 * s_
    const A = 1.9779984951 * l_ - 2.428592205 * m_ + 0.4505937099 * s_
    const B = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.808675766 * s_
    const c = Math.sqrt(A * A + B * B)
    const h = ((Math.atan2(B, A) * 180) / Math.PI + 360) % 360
    return { l: L, c, h }
}

function relLuminance(hex: string): number {
    const v = hex.replace('#', '')
    const ch = (i: number) => {
        const x = parseInt(v.slice(i, i + 2), 16) / 255
        return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4
    }
    return 0.2126 * ch(0) + 0.7152 * ch(2) + 0.0722 * ch(4)
}

// Contraste WCAG entre duas cores hex (1 a 21).
export function contrastRatio(a: string, b: string): number {
    const [hi, lo] = [relLuminance(a), relLuminance(b)].sort((x, y) => y - x)
    return (hi + 0.05) / (lo + 0.05)
}

// Contraste de uma cor com texto branco (o destaque vira fundo de botão com texto branco).
export function contrastWithWhite(hex: string): number {
    return 1.05 / (relLuminance(hex) + 0.05)
}

// Escurece a cor (em OKLCH, sem mudar a matiz) até passar 4.5:1 com texto branco.
export function accentForWhiteText(hex: string): string {
    const { l, c, h } = hexToOklch(hex)
    let L = l
    let out = hex.toLowerCase()
    for (let i = 0; i < 40 && contrastWithWhite(out) < 4.5 && L > 0.2; i++) {
        L -= 0.015
        out = oklchToHex(L, Math.min(c, 0.2), h)
    }
    return out
}

// Mesma cor, mais escura (hover de botão).
export function darken(hex: string, amount: number): string {
    const { l, c, h } = hexToOklch(hex)
    return oklchToHex(Math.max(0, l - amount), c, h)
}

// ─── Motor ───────────────────────────────────────────────────────────────────

const clamp01 = (v: number) => Math.min(1, Math.max(0, v))

// Hierarquia de camadas (igual nos dois modos):
// - background.secondary: moldura do app (barra lateral)
// - background.primary: painel de conteúdo
// - surface.secondary: cartões e listas sobre o conteúdo
// - surface.tertiary / background.tertiary: campos, hover, menus
// - surface.elevated / background.elevated: modais e popovers
export function buildSemanticColors(p: ThemePreset): SemanticColors {
    const k = p.contrast
    const n = (l: number, chromaScale = 1) => oklchToHex(clamp01(l), p.chroma * chromaScale, p.hue)

    if (p.mode === 'dark') {
        const L = p.base
        const step = 0.028 * k
        return {
            background: {
                primary: n(L),
                secondary: n(L - step * 0.75),
                tertiary: n(L + step * 2),
                elevated: n(L + step * 1.6),
            },
            text: {
                // Texto relativo ao fundo: temas escuros mais claros (Nord, Dracula...) pedem texto mais claro.
                primary: n(Math.min(0.97, Math.max(0.93, L + 0.66) + 0.03 * (k - 1)), 0.4),
                secondary: n(Math.min(0.9, Math.max(0.76, L + 0.53) + 0.04 * (k - 1)), 0.6),
                tertiary: n(Math.min(0.84, Math.max(0.68, L + 0.47) + 0.04 * (k - 1)), 0.7),
                disabled: n(0.5, 0.7),
            },
            border: {
                primary: n(L + step * 2.6),
                secondary: n(L + step * 1.5),
            },
            surface: {
                primary: n(L - step * 0.75),
                secondary: n(L + step),
                tertiary: n(L + step * 2),
                elevated: n(L + step * 1.6),
            },
        }
    }

    const L = p.base
    const step = 0.02 * k
    return {
        background: {
            primary: n(L),
            secondary: n(L - step),
            tertiary: n(L - step * 2.4),
            elevated: n(Math.min(0.997, L + 0.025), 0.35),
        },
        text: {
            primary: n(0.24 - 0.04 * (k - 1), 0.8),
            secondary: n(0.45 - 0.05 * (k - 1), 0.8),
            tertiary: n(0.52 - 0.05 * (k - 1), 0.8),
            disabled: n(0.68),
        },
        border: {
            primary: n(L - step * 3.6),
            secondary: n(L - step * 5),
        },
        surface: {
            primary: n(L - step),
            secondary: n(L - step * 1.2),
            tertiary: n(L - step * 2.4),
            elevated: n(Math.min(0.997, L + 0.025), 0.35),
        },
    }
}

// ─── Catálogo ────────────────────────────────────────────────────────────────

export const DEFAULT_THEME: Record<ThemeMode, string> = { light: 'light-default', dark: 'dark-default' }

// Os padrões do LexHub: as cores do tokens.css (para a miniatura) e o destaque da marca.
const BUILT_IN: Record<string, { name: string; mode: ThemeMode; preview: ThemePreview }> = {
    'light-default': {
        name: 'Claro Padrão',
        mode: 'light',
        preview: {
            bg: '#f4f5f7',
            sidebar: '#11151a',
            sideText: '#c9ced6',
            card: '#ffffff',
            text: '#15181d',
            border: '#e3e6eb',
            accent: '#b35500',
        },
    },
    'dark-default': {
        name: 'Escuro Padrão',
        mode: 'dark',
        preview: {
            bg: '#14110e',
            sidebar: '#0f0c0a',
            sideText: '#d6cbbe',
            card: '#1c1814',
            text: '#f2ebe3',
            border: '#2f2922',
            accent: '#f5a04a',
        },
    },
}

// Temas do LexFlow (mesma ordem, ids, nomes, fundo e destaque). Os dois "default" daqui são trocados
// pelos padrões do LexHub acima.
const THEME_SEEDS: readonly {
    id: string
    name: string
    mode: ThemeMode
    bg: string
    accent: string
    contrast?: number
}[] = [
    // ── Claros
    { id: 'light-default', name: 'Claro Padrão', mode: 'light', bg: '#f1f3f4', accent: '#1a73e8' },
    { id: 'light-github', name: 'GitHub Light', mode: 'light', bg: '#f6f8fa', accent: '#0969da' },
    { id: 'light-warm', name: 'Claro Quente', mode: 'light', bg: '#f5f0eb', accent: '#b45309' },
    { id: 'light-one-light', name: 'One Light', mode: 'light', bg: '#f4f4f5', accent: '#4078f2' },
    { id: 'light-catppuccin', name: 'Catppuccin Latte', mode: 'light', bg: '#eff1f5', accent: '#8839ef' },
    { id: 'light-rose-pine', name: 'Rosé Pine Dawn', mode: 'light', bg: '#faf4ed', accent: '#907aa9' },
    { id: 'light-gruvbox', name: 'Gruvbox Light', mode: 'light', bg: '#f6eccb', accent: '#458588' },
    { id: 'light-tokyo-day', name: 'Tokyo Day', mode: 'light', bg: '#e6e7ed', accent: '#2e7de9' },
    { id: 'light-solarized', name: 'Solarized Light', mode: 'light', bg: '#fbf3df', accent: '#268bd2' },
    { id: 'light-owl', name: 'Light Owl', mode: 'light', bg: '#f6f6f8', accent: '#4876d6' },
    { id: 'light-ayu', name: 'Ayu Light', mode: 'light', bg: '#f8f8f8', accent: '#fa8d3e' },
    { id: 'light-quiet', name: 'Quiet Light', mode: 'light', bg: '#f3f3f3', accent: '#705697' },
    { id: 'light-noctis-lux', name: 'Noctis Lux', mode: 'light', bg: '#fbf5e9', accent: '#16a3b6' },
    { id: 'light-everforest', name: 'Everforest Light', mode: 'light', bg: '#f8f2df', accent: '#8da101' },
    {
        id: 'light-high-contrast',
        name: 'Alto Contraste Claro',
        mode: 'light',
        bg: '#f2f4f7',
        accent: '#2563eb',
        contrast: 1.6,
    },
    // ── Escuros
    { id: 'dark-default', name: 'Escuro Padrão', mode: 'dark', bg: '#191b1f', accent: '#5b9cf6' },
    { id: 'dark-github', name: 'GitHub Dark', mode: 'dark', bg: '#0d1117', accent: '#58a6ff' },
    { id: 'dark-dimmed', name: 'GitHub Dimmed', mode: 'dark', bg: '#22272e', accent: '#539bf5' },
    { id: 'dark-one-dark', name: 'One Dark Pro', mode: 'dark', bg: '#282c34', accent: '#61afef' },
    { id: 'dark-tokyo-night', name: 'Tokyo Night', mode: 'dark', bg: '#1a1b26', accent: '#7aa2f7' },
    { id: 'dark-tokyo-storm', name: 'Tokyo Night Storm', mode: 'dark', bg: '#24283b', accent: '#7aa2f7' },
    { id: 'dark-catppuccin', name: 'Catppuccin', mode: 'dark', bg: '#1e1e2e', accent: '#cba6f7' },
    { id: 'dark-catppuccin-frappe', name: 'Catppuccin Frappé', mode: 'dark', bg: '#303446', accent: '#ca9ee6' },
    { id: 'dark-dracula', name: 'Dracula', mode: 'dark', bg: '#282a36', accent: '#bd93f9' },
    { id: 'dark-dracula-soft', name: 'Dracula Soft', mode: 'dark', bg: '#22212c', accent: '#bd93f9' },
    { id: 'dark-monokai', name: 'Monokai Pro', mode: 'dark', bg: '#2d2a2e', accent: '#a9dc76' },
    { id: 'dark-one-monokai', name: 'One Monokai', mode: 'dark', bg: '#282c34', accent: '#528bff' },
    { id: 'dark-nord', name: 'Nord', mode: 'dark', bg: '#2e3440', accent: '#88c0d0' },
    { id: 'dark-solarized', name: 'Solarized Dark', mode: 'dark', bg: '#002b36', accent: '#268bd2' },
    { id: 'dark-omni', name: 'Omni', mode: 'dark', bg: '#191622', accent: '#988bc7' },
    { id: 'dark-shades-purple', name: 'Shades of Purple', mode: 'dark', bg: '#2d2b55', accent: '#7b5cff' },
    { id: 'dark-night-owl', name: 'Night Owl', mode: 'dark', bg: '#011627', accent: '#82aaff' },
    { id: 'dark-palenight', name: 'Material Palenight', mode: 'dark', bg: '#292d3e', accent: '#c792ea' },
    { id: 'dark-ayu', name: 'Ayu Dark', mode: 'dark', bg: '#10141c', accent: '#e6b450' },
    { id: 'dark-panda', name: 'Panda Syntax', mode: 'dark', bg: '#292a2b', accent: '#19f9d8' },
    { id: 'dark-rose-pine-moon', name: 'Rosé Pine Moon', mode: 'dark', bg: '#232136', accent: '#c4a7e7' },
    { id: 'dark-everforest', name: 'Everforest', mode: 'dark', bg: '#2d353b', accent: '#a7c080' },
    { id: 'dark-synthwave', name: 'SynthWave 84', mode: 'dark', bg: '#262335', accent: '#ff7edb' },
    { id: 'dark-noctis-obscuro', name: 'Noctis Obscuro', mode: 'dark', bg: '#031417', accent: '#49ace9' },
    { id: 'dark-gruvbox', name: 'Gruvbox Dark', mode: 'dark', bg: '#282828', accent: '#fe8019' },
    { id: 'dark-midnight', name: 'Meia-noite', mode: 'dark', bg: '#131927', accent: '#5b5bd6' },
    { id: 'dark-high-contrast', name: 'Alto Contraste', mode: 'dark', bg: '#0a0a0a', accent: '#3b82f6', contrast: 1.5 },
]

// Limites de luminosidade da camada de conteúdo, para nenhum tema ficar ilegível.
const BASE_LIMITS: Record<ThemeMode, [number, number]> = { light: [0.93, 0.992], dark: [0.17, 0.34] }

export const THEME_PRESETS: ThemePreset[] = THEME_SEEDS.map((seed) => {
    const builtIn = BUILT_IN[seed.id]
    const { l, c, h } = hexToOklch(seed.bg)
    const [min, max] = BASE_LIMITS[seed.mode]
    return {
        id: seed.id,
        name: builtIn?.name ?? seed.name,
        mode: seed.mode,
        hue: h,
        chroma: Math.min(c, seed.mode === 'dark' ? 0.07 : 0.05),
        base: Math.min(max, Math.max(min, l)),
        contrast: seed.contrast ?? 1,
        accent: builtIn ? builtIn.preview.accent : accentForWhiteText(seed.accent),
        builtIn: !!builtIn,
    }
})

export function findTheme(id: string | null | undefined): ThemePreset | undefined {
    return id ? THEME_PRESETS.find((t) => t.id === id) : undefined
}

export function isValidThemeId(id: string | null | undefined, mode: ThemeMode): boolean {
    return findTheme(id)?.mode === mode
}

// Cores da miniatura da galeria (sem depender das variáveis da página). Id desconhecido = Claro Padrão.
export function themePreview(id: string): ThemePreview {
    const theme = findTheme(id) ?? findTheme(DEFAULT_THEME.light)!
    const builtIn = BUILT_IN[theme.id]
    if (builtIn) return { ...builtIn.preview }
    const c = buildSemanticColors(theme)
    return {
        bg: c.background.primary,
        sidebar: c.background.secondary,
        sideText: c.text.secondary,
        card: theme.mode === 'light' ? c.surface.elevated : c.surface.secondary,
        text: c.text.primary,
        border: c.border.primary,
        accent: theme.accent,
    }
}

// ─── Cores de destaque ───────────────────────────────────────────────────────

// "Do tema" usa a cor de cada tema (padrão); as demais fixam uma cor em qualquer tema (todas passam
// 4.5:1 com texto branco). A pessoa também pode escolher qualquer cor: guardada como hex ('#e11d48').
export const THEME_ACCENTS: readonly { id: string; name: string; hex: string | null }[] = [
    { id: 'tema', name: 'Do tema', hex: null },
    { id: 'indigo', name: 'Índigo', hex: '#5b5bd6' },
    { id: 'azul', name: 'Azul', hex: '#2563eb' },
    { id: 'ciano', name: 'Ciano', hex: '#0e7490' },
    { id: 'petroleo', name: 'Petróleo', hex: '#0f766e' },
    { id: 'verde', name: 'Verde', hex: '#0f7a5c' },
    { id: 'oliva', name: 'Oliva', hex: '#4d7c0f' },
    { id: 'cobre', name: 'Cobre', hex: '#b4540a' },
    { id: 'laranja', name: 'Laranja', hex: '#c2410c' },
    { id: 'vermelho', name: 'Vermelho', hex: '#dc2626' },
    { id: 'rosa', name: 'Rosa', hex: '#db2777' },
    { id: 'magenta', name: 'Magenta', hex: '#c026d3' },
    { id: 'violeta', name: 'Violeta', hex: '#7c3aed' },
    { id: 'ardosia', name: 'Ardósia', hex: '#5b6b80' },
    { id: 'grafite', name: 'Grafite', hex: '#3f3f46' },
]

const HEX_RE = /^#[0-9a-f]{6}$/i

export function isCustomAccent(id: string | null | undefined): boolean {
    return !!id && HEX_RE.test(id)
}

export function isValidAccentId(id: string | null | undefined): boolean {
    return !!id && (isCustomAccent(id) || THEME_ACCENTS.some((a) => a.id === id))
}

// true = a escolha é "Do tema" (inclui nada escolhido e id desconhecido).
export function isThemeAccent(id: string | null | undefined): boolean {
    if (isCustomAccent(id)) return false
    return !THEME_ACCENTS.find((a) => a.id === id)?.hex
}

// Hex final do destaque para uma escolha e a cor do tema.
export function resolveAccentHex(accent: string | null | undefined, themeAccent: string): string {
    if (accent && isCustomAccent(accent)) return accent.toLowerCase()
    return THEME_ACCENTS.find((a) => a.id === accent)?.hex ?? themeAccent
}
