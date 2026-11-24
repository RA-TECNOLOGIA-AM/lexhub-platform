import { useAsync } from '../../hooks/useAsync.ts'
import { dataClient } from '../../services/client.ts'
import type { HiddenDashboard, SupportSession } from '../../types/index.ts'
import { HIDDEN_REASON } from './hiddenReason.ts'

const firstName = (name: string) => name.trim().split(/\s+/)[0] ?? name

// A lista em si, sem buscar nada (testada em HiddenForMember.test.tsx). Recolhida por padrão.
export function HiddenForMemberView({ name, items }: { name: string; items: HiddenDashboard[] }) {
    const first = firstName(name)
    return (
        <details className="card hidden-for-member">
            <summary className="h2">
                Dashboards ocultos para {first} ({items.length})
            </summary>
            {items.length === 0 ? (
                <p className="muted small">Nenhum dashboard desta unidade está oculto para {first}.</p>
            ) : (
                <ul className="hidden-list">
                    {items.map((d) => (
                        <li key={d.key}>
                            <strong>{d.title}</strong> <span className="muted small">· {d.area}</span>
                            <div className="small">{HIDDEN_REASON[d.reason] ?? d.reason}</div>
                        </li>
                    ))}
                </ul>
            )}
        </details>
    )
}

// Módulo: no hub em modo suporte, "por que o membro não vê" — os dashboards da unidade escolhida que estão
// ocultos para ele, com o motivo. Só aparece com uma unidade escolhida; falhou = não mostra nada.
export function HiddenForMember({ org, session, unit }: { org: string; session: SupportSession; unit: string }) {
    const { data } = useAsync(
        () => dataClient.listHiddenForMember(org, session.sessionId, unit),
        [org, session.sessionId, unit],
    )
    if (!data) return null
    return <HiddenForMemberView name={session.member.name} items={data} />
}
