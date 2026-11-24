import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../../contexts/auth-context.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { timeAgo } from '../../lib/format.ts'
import { dataClient } from '../../services/client.ts'
import { Icon, type IconName } from '../ui/Icon.tsx'
import { groupSessions, type DeviceGroup, type DeviceKind } from './devices.ts'

const KIND_ICON: Record<DeviceKind, IconName> = { computer: 'monitor', phone: 'phone', tv: 'tv' }
const CONFIRM_MS = 4000

// Botão de duas etapas (igual ao LexFlow): o 1º clique vira "Confirmar?", o 2º executa; volta sozinho.
function ConfirmButton({ label, onConfirm, disabled }: { label: string; onConfirm: () => void; disabled?: boolean }) {
    const [armed, setArmed] = useState(false)
    const timer = useRef<ReturnType<typeof setTimeout>>(undefined)
    useEffect(() => () => clearTimeout(timer.current), [])
    return (
        <button
            type="button"
            className={`btn btn-sm ${armed ? 'btn-danger' : 'btn-ghost'}`}
            disabled={disabled}
            onClick={() => {
                clearTimeout(timer.current)
                if (armed) {
                    setArmed(false)
                    onConfirm()
                    return
                }
                setArmed(true)
                timer.current = setTimeout(() => setArmed(false), CONFIRM_MS)
            }}
        >
            {armed ? 'Confirmar?' : label}
        </button>
    )
}

type DevicesListProps = {
    groups: DeviceGroup[]
    now: number
    busy: boolean
    onRevoke: (group: DeviceGroup) => void
    onRevokeOthers: () => void
    onSignOut: () => void
}

// A lista em si (sem buscar nada): "Este dispositivo" no topo, depois os outros aparelhos.
export function DevicesList({ groups, now, busy, onRevoke, onRevokeOthers, onSignOut }: DevicesListProps) {
    const hasOthers = groups.some((g) => !g.current)
    return (
        <>
            <ul className="settings-card devices-list">
                {groups.map((g) => (
                    <li key={g.key} className="devices-row">
                        <span className="devices-icon" aria-hidden="true">
                            <Icon name={KIND_ICON[g.kind]} size={20} />
                        </span>
                        <div className="devices-info">
                            <p className="devices-name">
                                {g.label}
                                {g.current && <span className="devices-badge">Este dispositivo</span>}
                            </p>
                            <p className="muted small">
                                {[
                                    g.ip,
                                    g.current ? 'ativo agora' : `ativo ${timeAgo(g.lastActiveAt, now)}`,
                                    g.ids.length > 1 ? `${g.ids.length} sessões` : null,
                                ]
                                    .filter(Boolean)
                                    .join(' · ')}
                            </p>
                        </div>
                        {g.current ? (
                            <ConfirmButton label="Sair deste dispositivo" onConfirm={onSignOut} disabled={busy} />
                        ) : (
                            <ConfirmButton label="Desconectar" onConfirm={() => onRevoke(g)} disabled={busy} />
                        )}
                    </li>
                ))}
            </ul>
            {hasOthers ? (
                <div>
                    <ConfirmButton label="Desconectar todos os outros" onConfirm={onRevokeOthers} disabled={busy} />
                </div>
            ) : (
                <p className="muted small">A sua conta não está aberta em nenhum outro aparelho.</p>
            )}
        </>
    )
}

// Módulo: Configurações → Dispositivos. Onde a conta está aberta, e derrubar um aparelho, todos os outros
// ou este (= sair). O aparelho derrubado percebe em até 1 minuto (usePresenceHeartbeat) e vai ao login.
export function DevicesSection() {
    const { signOut } = useAuth()
    const [version, setVersion] = useState(0) // +1 = buscar de novo (depois de desconectar)
    const [busy, setBusy] = useState(false)
    const [actionError, setActionError] = useState('')
    // A hora vem junto com a lista: "ativo há 5 min" fica fixo até a próxima busca.
    const sessions = useAsync(
        async () => ({ groups: groupSessions(await dataClient.listMySessions()), at: Date.now() }),
        [version],
    )
    const error = actionError || (sessions.error ? 'Não foi possível carregar os aparelhos. Tente de novo.' : '')

    async function run(action: () => Promise<unknown>, failure: string) {
        setBusy(true)
        setActionError('')
        try {
            await action()
        } catch {
            setActionError(failure)
        }
        setVersion((v) => v + 1)
        setBusy(false)
    }

    return (
        <div className="settings-stack">
            <p className="muted">
                Onde a sua conta está aberta. Um aparelho desconectado sai em até 1 minuto e precisa entrar de novo.
            </p>
            {error && (
                <p className="small settings-warn" role="status">
                    {error}
                </p>
            )}
            {!sessions.data && sessions.loading && <p className="muted small">Carregando…</p>}
            {sessions.data && (
                <DevicesList
                    groups={sessions.data.groups}
                    now={sessions.data.at}
                    busy={busy}
                    onRevoke={(g) =>
                        void run(
                            () => Promise.all(g.ids.map((id) => dataClient.revokeMySession(id))),
                            'Não foi possível desconectar o aparelho.',
                        )
                    }
                    onRevokeOthers={() =>
                        void run(() => dataClient.signOutOthers(), 'Não foi possível desconectar os outros aparelhos.')
                    }
                    onSignOut={() => void signOut()}
                />
            )}
        </div>
    )
}
