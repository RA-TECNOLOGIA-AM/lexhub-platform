import { useEffect } from 'react'
import { dataClient } from '../services/client.ts'

// De quanto em quanto tempo avisa "estou aqui" (Membros mostra "Online agora" até ONLINE_MS sem aviso).
export const HEARTBEAT_MS = 60_000

// Módulo: avisa o servidor que quem está logado está com o LexHub aberto (api.touch_presence grava
// last_seen_at). Parâmetro: enabled (só depois do login). Esconde: o relógio, a aba escondida (não avisa;
// ao voltar, avisa na hora) e as falhas (presença é detalhe: nunca mostra erro nem quebra a tela).
export function usePresenceHeartbeat(enabled: boolean): void {
    useEffect(() => {
        if (!enabled || typeof document === 'undefined') return
        const beat = () => {
            if (document.visibilityState !== 'visible') return
            dataClient.touchPresence().catch(() => {})
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
