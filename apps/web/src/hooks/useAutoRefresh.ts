import { useEffect, useRef } from 'react'

// Quanto o relógio confere se já deu a hora (a busca sai no máximo isso depois de vencer).
const CHECK_MS = 30_000

// Módulo: chama `refresh` quando o que está na tela passou de `everyMs`, como um "Atualizar" automático.
// Parâmetros: a validade (ms), o que fazer para buscar de novo e `loadedAt` — qualquer valor que muda
// quando chega um dado novo (o próprio resultado); o prazo conta a partir daí, então "Atualizar",
// período e filtros também reiniciam a contagem.
// Esconde: o relógio, a aba escondida (não busca; ao voltar, busca se venceu) e a busca em andamento
// (dispara uma vez só por dado; a próxima só depois de o novo chegar — a do LexPre leva até ~50 s).
export function useAutoRefresh(everyMs: number, refresh: () => void, loadedAt: unknown): void {
    const refreshRef = useRef(refresh)
    useEffect(() => {
        refreshRef.current = refresh
    })

    useEffect(() => {
        if (typeof document === 'undefined') return
        const startedAt = Date.now()
        let fired = false
        const check = () => {
            if (fired || document.visibilityState !== 'visible') return
            if (Date.now() - startedAt < everyMs) return
            fired = true
            refreshRef.current()
        }
        const timer = setInterval(check, Math.min(everyMs, CHECK_MS))
        document.addEventListener('visibilitychange', check)
        return () => {
            clearInterval(timer)
            document.removeEventListener('visibilitychange', check)
        }
    }, [everyMs, loadedAt])
}
