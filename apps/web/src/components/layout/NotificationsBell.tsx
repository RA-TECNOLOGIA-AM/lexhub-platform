import { useCallback, useEffect, useRef, useState } from 'react'
import { Icon } from '../ui/Icon.tsx'
import { PageTransitionLink } from '../page_transition/PageTransitionLink.tsx'
import { useDismiss } from '../../hooks/useDismiss.ts'
import { refreshPendingRequests } from '../../hooks/usePendingRequests.ts'
import { dataClient } from '../../services/client.ts'
import { timeAgo } from '../../lib/format.ts'
import { bellCount } from '../../lib/notifications.ts'
import type { NotificationsResponse } from '../../types/index.ts'

type NotificationsBellProps = {
    staff: boolean // equipe RA: o painel também mostra os pedidos de acesso pendentes
    pending: number // quantos pedidos pendentes (usePendingRequests)
    onNavigate: () => void // ao abrir um item (ex.: fechar o menu do celular)
}

const EMPTY: NotificationsResponse = { items: [], unread: 0 }

// Módulo: o sino da topbar e o painel que ele abre.
// - Pedidos de acesso pendentes (equipe RA): uma linha fixa, calculada na hora; some quando ninguém espera.
// - Notificações guardadas (api.list_my_notifications): clicar marca como lida e leva ao link.
// Busca ao montar e toda vez que o painel abre (sem ficar consultando o banco em segundo plano).
export function NotificationsBell({ staff, pending, onNavigate }: NotificationsBellProps) {
    const [open, setOpen] = useState(false)
    const [data, setData] = useState<NotificationsResponse>(EMPTY)
    const [failed, setFailed] = useState(false)
    const root = useRef<HTMLDivElement>(null)
    const button = useRef<HTMLButtonElement>(null)

    // Ex.: a função ainda não existe no banco: o sino fica sem número, sem atrapalhar a tela.
    const load = useCallback(
        () =>
            dataClient.listMyNotifications().then(
                (next) => ({ next, failed: false }),
                () => ({ next: null, failed: true }),
            ),
        [],
    )
    const apply = ({ next, failed }: { next: NotificationsResponse | null; failed: boolean }) => {
        if (next) setData(next)
        setFailed(failed)
    }
    const refresh = () => load().then(apply)

    useEffect(() => {
        let ignore = false
        void load().then((result) => {
            if (!ignore) apply(result)
        })
        return () => {
            ignore = true
        }
    }, [load])

    useDismiss({
        open,
        onClose: () => setOpen(false),
        isInside: (target) => !!root.current?.contains(target),
        returnFocus: button,
    })

    function toggle() {
        const next = !open
        setOpen(next)
        if (next) {
            void refresh()
            if (staff) void refreshPendingRequests()
        }
    }

    // Marca na tela na hora (não espera o banco) e grava em seguida.
    function markRead(ids: string[] | null) {
        const at = new Date().toISOString()
        setData((prev) => {
            const items = prev.items.map((n) =>
                !n.read_at && (ids === null || ids.includes(n.id)) ? { ...n, read_at: at } : n,
            )
            const changed = prev.items.filter((n) => !n.read_at).length - items.filter((n) => !n.read_at).length
            return { items, unread: ids === null ? 0 : Math.max(0, prev.unread - changed) }
        })
        void dataClient.markNotificationsRead(ids).catch(() => refresh())
    }

    function close() {
        setOpen(false)
        onNavigate()
    }

    const count = bellCount(data.unread, pending)
    const empty = pending === 0 && data.items.length === 0

    return (
        <div className="notif" ref={root}>
            <button
                ref={button}
                className="iconbtn notif-btn"
                type="button"
                aria-label={count ? `Notificações (${count} novas)` : 'Notificações'}
                aria-expanded={open}
                aria-controls="notif-panel"
                onClick={toggle}
            >
                <Icon name="bell" />
                {count && (
                    <span className="notif-dot" aria-hidden="true">
                        {count}
                    </span>
                )}
            </button>

            {open && (
                <div id="notif-panel" className="notif-panel" role="dialog" aria-label="Notificações">
                    <div className="notif-head">
                        <strong>Notificações</strong>
                        {data.unread > 0 && (
                            <button className="linkbtn small" type="button" onClick={() => markRead(null)}>
                                Marcar todas como lidas
                            </button>
                        )}
                    </div>

                    <div className="notif-list">
                        {pending > 0 && (
                            <PageTransitionLink className="notif-item unread" to="/plataforma/pedidos" onClick={close}>
                                <span className="notif-icon">
                                    <Icon name="inbox" size={16} />
                                </span>
                                <span className="notif-text">
                                    <span className="notif-title">
                                        {pending === 1
                                            ? '1 pedido de acesso aguardando'
                                            : `${pending} pedidos de acesso aguardando`}
                                    </span>
                                    <span className="small muted">Aprove ou recuse em Pedidos de acesso.</span>
                                </span>
                            </PageTransitionLink>
                        )}

                        {data.items.map((n) => {
                            const content = (
                                <>
                                    <span className="notif-icon">
                                        <Icon name="check" size={16} />
                                    </span>
                                    <span className="notif-text">
                                        <span className="notif-title">{n.title}</span>
                                        {n.body && <span className="small muted">{n.body}</span>}
                                        <span className="small notif-when">{timeAgo(n.created_at)}</span>
                                    </span>
                                </>
                            )
                            const className = `notif-item${n.read_at ? '' : ' unread'}`
                            return n.link ? (
                                <PageTransitionLink
                                    key={n.id}
                                    className={className}
                                    to={n.link}
                                    onClick={() => {
                                        if (!n.read_at) markRead([n.id])
                                        close()
                                    }}
                                >
                                    {content}
                                </PageTransitionLink>
                            ) : (
                                <button
                                    key={n.id}
                                    className={className}
                                    type="button"
                                    onClick={() => !n.read_at && markRead([n.id])}
                                >
                                    {content}
                                </button>
                            )
                        })}

                        {empty && (
                            <p className="notif-empty small muted">
                                {failed ? 'Não foi possível carregar as notificações.' : 'Nada novo por aqui.'}
                            </p>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
