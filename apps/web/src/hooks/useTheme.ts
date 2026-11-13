import { useEffect, useState } from 'react'
import {
    applyTheme,
    oppositeTheme,
    resolveTheme,
    storedTheme,
    storeTheme,
    systemPrefersDark,
    type Theme,
} from '../lib/theme.ts'

// Hook: o tema atual e a troca (botão da topbar).
// Sem escolha guardada, acompanha o sistema ao vivo; depois de clicar, a escolha da pessoa manda.
export function useTheme(): { theme: Theme; toggle: () => void } {
    const [stored, setStored] = useState<Theme | null>(() => storedTheme())
    const [systemDark, setSystemDark] = useState(systemPrefersDark)
    const theme = resolveTheme(stored, systemDark)

    useEffect(() => {
        applyTheme(theme)
    }, [theme])

    useEffect(() => {
        if (stored) return
        const query = window.matchMedia('(prefers-color-scheme: dark)')
        const onChange = (event: MediaQueryListEvent) => setSystemDark(event.matches)
        query.addEventListener('change', onChange)
        return () => query.removeEventListener('change', onChange)
    }, [stored])

    const toggle = () => {
        const next = oppositeTheme(theme)
        storeTheme(next)
        setStored(next)
    }

    return { theme, toggle }
}
