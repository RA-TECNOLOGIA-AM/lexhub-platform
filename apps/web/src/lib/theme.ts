// Módulo: o tema da tela (claro ou escuro), sem React (testado em theme.test.ts).
// - A escolha da pessoa fica no localStorage; sem escolha, segue o sistema (prefers-color-scheme).
// - Aplicar = <html data-theme="light|dark">; as cores vêm das variáveis do tokens.css.
// O index.html repete readTheme/applyTheme num script curto antes do React, para não piscar claro ao abrir.

export type Theme = 'light' | 'dark'

export const THEME_KEY = 'lexhub.theme'

// A escolha guardada. Valor estranho ou storage bloqueado (aba privada) = sem escolha.
export function storedTheme(storage: Pick<Storage, 'getItem'> | null = safeLocal()): Theme | null {
    try {
        const value = storage?.getItem(THEME_KEY)
        return value === 'light' || value === 'dark' ? value : null
    } catch {
        return null
    }
}

export function storeTheme(theme: Theme, storage: Pick<Storage, 'setItem'> | null = safeLocal()): void {
    try {
        storage?.setItem(THEME_KEY, theme)
    } catch {
        // sem storage: vale só enquanto a página estiver aberta
    }
}

// O tema que vale: a escolha da pessoa manda; sem ela, o do sistema.
export function resolveTheme(stored: Theme | null, systemDark: boolean): Theme {
    return stored ?? (systemDark ? 'dark' : 'light')
}

export function oppositeTheme(theme: Theme): Theme {
    return theme === 'dark' ? 'light' : 'dark'
}

export function applyTheme(theme: Theme, root: HTMLElement = document.documentElement): void {
    root.dataset.theme = theme
}

export function systemPrefersDark(): boolean {
    try {
        return window.matchMedia('(prefers-color-scheme: dark)').matches
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
