import { useCallback, useEffect, useLayoutEffect, useMemo, useState, type ReactNode } from 'react'
import { useLocation, useNavigate } from 'react-router'
import { expireSupport, onSupportExpired, setSupport, supportValidFor } from '../lib/supportSession.ts'
import { dataClient } from '../services/client.ts'
import { SupportContext, useSupportSession, type SupportState } from './support-context.ts'

const EXPIRED = 'A sessão de suporte venceu'

// Para onde Sair (e o vencimento) leva: a gaveta do membro em Membros.
const membersOf = (org: string, membershipId: string) => `/${org}/admin/membros?m=${membershipId}`

// Módulo: o modo suporte na tela (Owner/Dev vendo como um membro, só leitura).
// Esconde: onde a sessão mora (lib/supportSession.ts), a conferência da sessão restaurada (outra org ou
// vencida = sai sem avisar), o relógio que sai sozinho no expiresAt e o aviso quando a API responde 409.
// Devolve (useSupport): a sessão, start, exit e o aviso "A sessão de suporte venceu".
export function SupportProvider({ children }: { children: ReactNode }) {
    const stored = useSupportSession()
    const { pathname } = useLocation()
    const navigate = useNavigate()
    const [notice, setNotice] = useState<string | null>(null)
    // Restaurada do sessionStorage, mas de outra org (ou já vencida): nem chega às telas.
    const session = stored && supportValidFor(stored, pathname) ? stored : null

    // Layout effect: roda antes dos efeitos das telas (que buscam dados), então o cabeçalho de suporte
    // nunca sai para outra organização nem depois do prazo.
    useLayoutEffect(() => {
        if (stored && !session) setSupport(null)
    }, [stored, session])

    // Venceu (409 da API ou o relógio abaixo): avisa e volta à gaveta do membro.
    useEffect(
        () =>
            onSupportExpired((ended) => {
                setNotice(EXPIRED)
                navigate(membersOf(ended.org, ended.member.membershipId), { replace: true })
            }),
        [navigate],
    )

    // Relógio local: sai sozinho no expiresAt, mesmo sem nenhuma chamada à API.
    useEffect(() => {
        if (!session) return
        const timer = setTimeout(() => expireSupport(), Math.max(0, Date.parse(session.expiresAt) - Date.now()))
        return () => clearTimeout(timer)
    }, [session])

    const start = useCallback(
        async (membershipId: string, name: string, reason: string) => {
            const org = pathname.split('/')[1] ?? ''
            const started = await dataClient.startSupport(org, membershipId, reason)
            // O nome vem do servidor; o da tela só cobre uma resposta sem nome.
            setSupport({ ...started, member: { ...started.member, name: started.member.name || name } })
            setNotice(null)
            navigate(`/${org}/dashboards`)
        },
        [pathname, navigate],
    )

    const exit = useCallback(async () => {
        if (!session) return
        await dataClient.endSupport(session.org, session.sessionId).catch(() => {}) // falhou: a sessão vence sozinha
        setSupport(null)
        navigate(membersOf(session.org, session.member.membershipId))
    }, [session, navigate])

    const value = useMemo<SupportState>(
        () => ({ session, start, exit, notice, clearNotice: () => setNotice(null) }),
        [session, start, exit, notice],
    )
    return <SupportContext value={value}>{children}</SupportContext>
}
