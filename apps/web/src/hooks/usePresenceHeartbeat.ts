import { useEffect, useRef } from 'react'
import { dataClient } from '../services/client.ts'

// De quanto em quanto tempo avisa "estou aqui" (Membros mostra "Online agora" até ONLINE_MS sem aviso).
export const HEARTBEAT_MS = 60_000

type BeatDeps = {
    touch: () => Promise<void>
    isAlive: () => Promise<boolean>
    onSessionGone: () => void
}

// Uma batida: avisa presença e confere se a sessão ainda existe no servidor (Configurações → Dispositivos
// pode tê-la derrubado de outro aparelho). Sessão morta chama onSessionGone uma vez só; falha de rede não
// conta como morta (isAlive já responde true na dúvida) e a presença nunca mostra erro.
export function createBeat({ touch, isAlive, onSessionGone }: BeatDeps): () => Promise<void> {
    let gone = false
    return async () => {
        if (gone) return
        touch().catch(() => {})
        const alive = await isAlive().catch(() => true)
        if (alive || gone) return
        gone = true
        onSessionGone()
    }
}

// Módulo: avisa o servidor que quem está logado está com o LexHub aberto (api.touch_presence grava
// last_seen_at) e, na mesma batida, percebe em até 1 minuto que a sessão foi derrubada.
// Parâmetros: enabled (só depois do login) e onSessionGone (o que fazer quando a sessão some).
// Esconde: o relógio, a aba escondida (não avisa; ao voltar, avisa na hora) e as falhas.
export function usePresenceHeartbeat(enabled: boolean, onSessionGone: () => void = () => {}): void {
    const gone = useRef(onSessionGone)
    useEffect(() => {
        gone.current = onSessionGone
    }, [onSessionGone])

    useEffect(() => {
        if (!enabled || typeof document === 'undefined') return
        const run = createBeat({
            touch: () => dataClient.touchPresence(),
            isAlive: () => dataClient.isSessionAlive(),
            onSessionGone: () => gone.current(),
        })
        const beat = () => {
            if (document.visibilityState !== 'visible') return
            void run()
        }
        beat()
        const timer = setInterval(beat, HEARTBEAT_MS)
        document.addEventListener('visibilitychange', beat)
        return () => {
            clearInterval(timer)
            document.removeEventListener('visibilitychange', beat)
        }
    }, [enabled])
}
