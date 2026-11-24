import { useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
    applyAppearance,
    cacheAppearance,
    normalizeAppearance,
    pickAppearance,
    readCachedAppearance,
    resolveAppearance,
    SYSTEM_DARK_QUERY,
    systemPrefersDark,
} from '../lib/appearance.ts'
import { createAppearanceSaver } from '../lib/appearanceSaver.ts'
import { dataClient } from '../services/client.ts'
import type { Appearance } from '../types/index.ts'
import { AppearanceContext, type AppearanceValue } from './appearance-context.ts'
import { useAuth } from './auth-context.ts'

// Módulo: a aparência da tela (Configurações → Aparência e o botão sol/lua), para o app inteiro.
// - Começa pela cópia local (a mesma que o index.html já aplicou antes do React: nada pisca).
// - Quando o /me chega: conta com alguma escolha manda; conta vazia mantém o que o aparelho tinha.
// - Cada mudança aplica na hora, atualiza a cópia local e, com alguém logado, salva na conta (em fila).
// - Sem modo escolhido, acompanha o claro/escuro do sistema ao vivo.
export function AppearanceProvider({ children }: { children: ReactNode }) {
    const { me } = useAuth()
    const signedIn = !!me
    const [appearance, setAppearance] = useState<Appearance>(() => readCachedAppearance())
    const [systemDark, setSystemDark] = useState(systemPrefersDark)
    const [saveError, setSaveError] = useState<string | null>(null)
    const save = useMemo(() => createAppearanceSaver((a) => dataClient.setMyAppearance(a), setSaveError), [])

    // O valor da conta, como texto: só reage quando a escolha salva muda de verdade
    // (o /me volta a cada troca de organização ou de foto, com o mesmo valor).
    const account = me?.user.appearance
    // Ajuste durante o render (padrão do React para "estado que segue uma prop"), sem efeito extra.
    const accountKey = account ? JSON.stringify(account) : null
    const [seenAccount, setSeenAccount] = useState<string | null>(null)
    if (account && accountKey !== seenAccount) {
        setSeenAccount(accountKey)
        setAppearance((local) => pickAppearance(local, normalizeAppearance(account)))
    }

    const resolved = useMemo(() => resolveAppearance(appearance, systemDark), [appearance, systemDark])

    // A escolha mais recente, mesmo antes do próximo render: cliques seguidos (ou o seletor de cor
    // arrastado) partem sempre da última mudança, nunca de uma cópia velha.
    const latest = useRef(appearance)

    useLayoutEffect(() => {
        latest.current = appearance
        applyAppearance(resolved)
        cacheAppearance(appearance)
    }, [resolved, appearance])

    useEffect(() => {
        if (appearance.mode) return
        const query = window.matchMedia(SYSTEM_DARK_QUERY)
        const onChange = (event: MediaQueryListEvent) => setSystemDark(event.matches)
        query.addEventListener('change', onChange)
        return () => query.removeEventListener('change', onChange)
    }, [appearance.mode])

    const value = useMemo<AppearanceValue>(() => {
        function change(patch: Partial<Appearance>) {
            const next = { ...latest.current, ...patch }
            latest.current = next
            setAppearance(next)
            if (signedIn) void save(next)
        }
        return {
            appearance,
            resolved,
            saveError,
            setMode: (mode) => change({ mode }),
            setTheme: (mode, id) => change({ [mode]: id }),
            setAccent: (accent) => change({ accent: accent.toLowerCase() }),
        }
    }, [appearance, resolved, saveError, save, signedIn])

    return <AppearanceContext value={value}>{children}</AppearanceContext>
}
