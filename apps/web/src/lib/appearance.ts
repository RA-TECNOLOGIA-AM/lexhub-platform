// Módulo: a aparência escolhida pela pessoa → modo + variáveis CSS no <html> (sem React, testado em appearance.test.ts).
// - O modo base continua em <html data-theme="light|dark"> (tokens.css): status, foco, links, toast, loader
//   e gráficos vêm sempre dele, já testados.
// - Um tema do motor (lib/themeEngine.ts) escreve só a parte neutra (fundos, bordas, texto, barra lateral)
//   e o destaque, como variáveis inline. Claro/Escuro Padrão com "Do tema" não escrevem nada (visual atual).
// - Cópia no localStorage (APPEARANCE_KEY): a escolha + as variáveis já calculadas dos dois modos, para o
//   index.html aplicar antes do React, sem piscar. A escolha "de verdade" fica na conta (app.profiles).

import type { Appearance, ThemeMode } from '../types/index.ts'
import {
    buildSemanticColors,
    contrastRatio,
    darken,
    DEFAULT_THEME,
    findTheme,
    isThemeAccent,
    isValidAccentId,
    isValidThemeId,
    resolveAccentHex,
    type ThemePreset,
} from './themeEngine.ts'

export const APPEARANCE_KEY = 'lexhub.appearance'
const LEGACY_THEME_KEY = 'lexhub.theme' // só o modo, gravado pelo botão sol/lua antigo

const NONE: Appearance = { mode: null, light: null, dark: null, accent: null }

// Tudo o que um tema pode escrever. Nada de status (--ok, --danger...), --focus, --link nem gráficos.
// O loading (--loader-*) só muda nos temas do motor: nos padrões fica a tela da marca.
export const MANAGED_VARS = [
    '--bg',
    '--surface',
    '--surface-2',
    '--surface-3',
    '--border',
    '--border-strong',
    '--border-hover',
    '--divider',
    '--text',
    '--text-2',
    '--text-muted',
    '--text-faint',
    '--side-bg',
    '--side-text',
    '--side-strong',
    '--side-line',
    '--side-item',
    '--side-hover',
    '--side-active',
    '--side-label',
    '--chip',
    '--on-chip',
    '--skel-mid',
    '--card-muted',
    '--accent',
    '--accent-hover',
    '--accent-soft',
    '--on-accent',
    '--loader-bg',
    '--loader-logo',
    '--loader-glow',
] as const

export type CssVars = Record<string, string>

export type ResolvedAppearance = {
    mode: ThemeMode
    themeId: string
    accentHex: string // o destaque que vale agora (mostrado na faixa da Cor de destaque)
    vars: CssVars // só as que mudam algo; vazio = visual do tokens.css
}

type Storage = { getItem(key: string): string | null; setItem(key: string, value: string): void }

// Valores fora do catálogo (tema removido, id do modo errado, hex mal formado) viram "sem escolha".
export function normalizeAppearance(a: Partial<Appearance> | null | undefined): Appearance {
    if (!a) return { ...NONE }
    return {
        mode: a.mode === 'light' || a.mode === 'dark' ? a.mode : null,
        light: isValidThemeId(a.light, 'light') ? a.light! : null,
        dark: isValidThemeId(a.dark, 'dark') ? a.dark! : null,
        accent: isValidAccentId(a.accent) ? a.accent!.toLowerCase() : null,
    }
}

export function resolveAppearance(a: Appearance, systemDark: boolean): ResolvedAppearance {
    const mode: ThemeMode = a.mode ?? (systemDark ? 'dark' : 'light')
    return resolveMode(a, mode)
}

function resolveMode(a: Appearance, mode: ThemeMode): ResolvedAppearance {
    const theme = findTheme(isValidThemeId(a[mode], mode) ? a[mode] : DEFAULT_THEME[mode])!
    const accentHex = resolveAccentHex(a.accent, theme.accent)
    const vars: CssVars = theme.builtIn ? {} : { ...neutralVars(theme), ...loaderVars(theme, accentHex) }
    if (!theme.builtIn || !isThemeAccent(a.accent)) Object.assign(vars, accentVars(accentHex))
    return { mode, themeId: theme.id, accentHex, vars }
}

// Cores do motor → tokens do LexHub. As camadas do LexFlow se distribuem diferente em cada modo
// (no claro a borda "secondary" é a mais forte; no escuro, a mais fraca).
function neutralVars(theme: ThemePreset): CssVars {
    const c = buildSemanticColors(theme)
    const shared = {
        '--bg': c.background.primary,
        '--text': c.text.primary,
        '--text-2': c.text.secondary,
        '--text-muted': c.text.tertiary,
        '--text-faint': c.text.disabled,
        '--border-hover': c.text.disabled,
        '--side-bg': c.background.secondary,
        '--side-text': c.text.secondary,
        '--side-strong': c.text.primary,
        '--side-label': c.text.tertiary,
        '--side-item': c.text.primary,
    }
    if (theme.mode === 'light') {
        return {
            ...shared,
            '--surface': c.surface.elevated,
            '--surface-2': mix(c.surface.elevated, c.background.primary),
            '--surface-3': c.background.secondary,
            '--border': c.border.primary,
            '--border-strong': c.border.secondary,
            '--divider': c.background.secondary,
            '--side-hover': c.background.tertiary,
            '--side-active': c.border.primary,
            '--side-line': c.border.primary,
            '--chip': c.text.secondary,
            '--on-chip': '#ffffff',
            '--skel-mid': c.border.primary,
            '--card-muted': mix(c.surface.elevated, c.background.primary),
        }
    }
    return {
        ...shared,
        '--surface': c.surface.secondary,
        '--surface-2': c.surface.elevated,
        '--surface-3': c.surface.tertiary,
        '--border': c.border.secondary,
        '--border-strong': c.border.primary,
        '--divider': c.surface.secondary,
        '--side-hover': c.surface.secondary,
        '--side-active': c.background.tertiary,
        '--side-line': c.background.tertiary,
        '--chip': c.background.tertiary,
        '--on-chip': c.text.primary,
        '--skel-mid': c.border.primary,
        '--card-muted': mix(c.surface.secondary, c.background.primary),
    }
}

// Loading (balança) no fundo do tema, com a cor de destaque; se o destaque quase some no fundo
// (ex.: Grafite num tema escuro), a balança usa a cor do texto.
function loaderVars(theme: ThemePreset, accentHex: string): CssVars {
    const c = buildSemanticColors(theme)
    const bg = c.background.primary
    const logo = contrastRatio(accentHex, bg) >= 3 ? accentHex : c.text.primary
    return { '--loader-bg': bg, '--loader-logo': logo, '--loader-glow': `${logo}55` }
}

// O destaque é sempre fundo de botão com texto branco (as cores prontas e as dos temas passam 4.5:1).
function accentVars(hex: string): CssVars {
    return {
        '--accent': hex,
        '--accent-hover': darken(hex, 0.06),
        '--accent-soft': `color-mix(in srgb, ${hex} 14%, var(--surface))`,
        '--on-accent': '#ffffff',
    }
}

// Média de duas cores hex em sRGB (cor "entre" duas camadas).
function mix(a: string, b: string): string {
    const channel = (hex: string, i: number) => parseInt(hex.slice(1 + i * 2, 3 + i * 2), 16)
    const out = [0, 1, 2].map((i) => Math.round((channel(a, i) + channel(b, i)) / 2))
    return `#${out.map((v) => v.toString(16).padStart(2, '0')).join('')}`
}

// Conta com alguma escolha manda; conta vazia não apaga o que este aparelho já tinha.
export function pickAppearance(local: Appearance, account: Appearance): Appearance {
    const hasAny = account.mode || account.light || account.dark || account.accent
    return hasAny ? account : local
}

// ─── Cópia local ─────────────────────────────────────────────────────────────

export function readCachedAppearance(storage: Pick<Storage, 'getItem'> | null = safeLocal()): Appearance {
    try {
        const raw = storage?.getItem(APPEARANCE_KEY)
        if (raw) return normalizeAppearance((JSON.parse(raw) as { prefs?: Appearance }).prefs)
        const legacy = storage?.getItem(LEGACY_THEME_KEY)
        return { ...NONE, mode: legacy === 'light' || legacy === 'dark' ? legacy : null }
    } catch {
        return { ...NONE }
    }
}

export function cacheAppearance(a: Appearance, storage: Pick<Storage, 'setItem'> | null = safeLocal()): void {
    try {
        const value = { prefs: a, light: resolveMode(a, 'light').vars, dark: resolveMode(a, 'dark').vars }
        storage?.setItem(APPEARANCE_KEY, JSON.stringify(value))
    } catch {
        // sem storage: vale enquanto a página estiver aberta (e a conta guarda a escolha)
    }
}

// ─── DOM ─────────────────────────────────────────────────────────────────────

export function applyAppearance(r: ResolvedAppearance, root: HTMLElement = document.documentElement): void {
    root.dataset.theme = r.mode
    for (const name of MANAGED_VARS) {
        const value = r.vars[name]
        if (value) root.style.setProperty(name, value)
        else root.style.removeProperty(name)
    }
}

export const SYSTEM_DARK_QUERY = '(prefers-color-scheme: dark)'

export function systemPrefersDark(): boolean {
    try {
        return window.matchMedia(SYSTEM_DARK_QUERY).matches
    } catch {
        return false
    }
}

function safeLocal(): Storage | null {
    try {
        return window.localStorage
    } catch {
        return null
    }
}
