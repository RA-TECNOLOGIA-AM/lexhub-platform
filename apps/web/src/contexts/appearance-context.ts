import { createContext, useContext } from 'react'
import type { ResolvedAppearance } from '../lib/appearance.ts'
import type { Appearance, ThemeMode } from '../types/index.ts'

export type AppearanceValue = {
    appearance: Appearance // a escolha da pessoa (null = sem escolha naquele campo)
    resolved: ResolvedAppearance // o que vale agora: modo, tema, hex do destaque
    setMode(mode: ThemeMode): void
    setTheme(mode: ThemeMode, id: string): void // tema da galeria daquele modo
    setAccent(accent: string): void // 'tema' | id de cor pronta | '#rrggbb'
    saveError: string | null // a tela mudou, mas a conta não gravou (aviso discreto)
}

export const AppearanceContext = createContext<AppearanceValue | null>(null)

// Qualquer componente dentro do <AppearanceProvider> lê e troca a aparência com useAppearance().
export function useAppearance(): AppearanceValue {
    const value = useContext(AppearanceContext)
    if (!value) throw new Error('useAppearance() precisa estar dentro de <AppearanceProvider>')
    return value
}
