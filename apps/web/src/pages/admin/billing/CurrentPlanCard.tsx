import type { BillingResponse } from '../../../types/index.ts'
import { dayMonthLabel, joinPt, usagePct, usageTone } from './billingView.ts'

type CurrentPlanCardProps = {
    current: BillingResponse['current']
    title: string // "Plano Pro" ou "Em implantação"
    usage: BillingResponse['usage']
}

const STATUS = {
    active: { label: 'Ativo', badge: 'badge ok' },
    past_due: { label: 'Pagamento pendente', badge: 'badge warn' },
    canceled: { label: 'Cancelado', badge: 'badge neutral' },
}

// Módulo: o card do topo. Plano atual, renovação e uma barra por limite do plano.
export function CurrentPlanCard({ current, title, usage }: CurrentPlanCardProps) {
    const status = STATUS[current.status]
    return (
        <section className="card card-pad stack" aria-label="Plano atual">
            <div className="row" style={{ justifyContent: 'space-between' }}>
                <div className="row" style={{ gap: 8 }}>
                    <h2 className="h2" style={{ color: 'var(--text)' }}>
                        {title}
                    </h2>
                    <span className={status.badge}>{status.label}</span>
                </div>
                <span className="muted small">
                    Renova em {dayMonthLabel(current.renewsOn)} · {joinPt(current.paymentMethods)} via{' '}
                    {current.gateway ?? '[GATEWAY]'}
                </span>
            </div>
            <div className="usage-grid">
                {usage.map((u) => (
                    <div key={u.key} className="usage">
                        <div className="usage-head small">
                            <span className="muted">{u.label}</span>
                            <span style={{ fontWeight: 500 }}>
                                {u.used} de {u.total}
                                {u.unit ? ` ${u.unit}` : ''}
                            </span>
                        </div>
                        <div
                            className="usage-track"
                            role="meter"
                            aria-label={u.label}
                            aria-valuemin={0}
                            aria-valuemax={u.total}
                            aria-valuenow={u.used}
                        >
                            <div
                                className={`usage-fill ${usageTone(u.used, u.total)}`}
                                style={{ width: `${usagePct(u.used, u.total)}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>
        </section>
    )
}
