import { useEffect, useState } from 'react'
import { useSupport } from '../../contexts/support-context.ts'
import { orgInitials } from '../../lib/orgs.ts'
import type { SupportSession } from '../../types/index.ts'
import { Avatar } from '../ui/Avatar.tsx'
import { Icon } from '../ui/Icon.tsx'

type SupportBannerViewProps = {
    session: SupportSession
    now: number // relógio (ms) para o "termina em"
    onExit: () => void
}

// Minutos que faltam, arredondados para cima (nunca negativo).
const minutesLeft = (expiresAt: string, now: number) => Math.max(0, Math.ceil((Date.parse(expiresAt) - now) / 60_000))

// A faixa em si, sem estado (testada em SupportBanner.test.tsx).
// No computador: "Vendo como {nome} · {motivo} · termina em {mm} min"; no celular, só o primeiro nome (CSS).
export function SupportBannerView({ session, now, onExit }: SupportBannerViewProps) {
    const { name, avatarPath, roleLabel } = session.member
    const first = name.trim().split(/\s+/)[0] ?? name
    return (
        <div className="support-bar" role="status">
            <Avatar user={{ name, initials: orgInitials(name), avatar_path: avatarPath }} className="av support-av" />
            <span className="support-text" title={roleLabel}>
                <span className="support-full">
                    Vendo como <strong>{name}</strong> · {session.reason} · termina em{' '}
                    {minutesLeft(session.expiresAt, now)} min
                </span>
                <span className="support-short">
                    Vendo como <strong>{first}</strong>
                </span>
            </span>
            <button
                className="btn btn-sm support-exit"
                type="button"
                aria-label="Sair do modo suporte"
                onClick={onExit}
            >
                <Icon name="logout" size={16} />
                Sair
            </button>
        </div>
    )
}

// Módulo: a faixa "Vendo como Fulano" no topo, enquanto durar o modo suporte (some fora dele).
// O tempo que falta anda a cada 30 s; Sair encerra a sessão e volta à gaveta do membro.
export function SupportBanner() {
    const { session, exit } = useSupport()
    const [now, setNow] = useState(() => Date.now())
    useEffect(() => {
        if (!session) return
        // A faixa já existia antes da sessão começar: acerta o relógio agora, senão mostra um minuto a mais.
        const tick = () => setNow(Date.now())
        const first = setTimeout(tick, 0)
        const timer = setInterval(tick, 30_000)
        return () => {
            clearTimeout(first)
            clearInterval(timer)
        }
    }, [session])
    if (!session) return null
    return <SupportBannerView session={session} now={now} onExit={() => void exit()} />
}
