import { Icon } from '../../../components/ui/Icon.tsx'
import type { ClientPlan, Plan } from '../../../types/index.ts'
import { planAction, priceLabel } from './billingView.ts'

type PlanCardProps = {
    plan: Plan
    current: ClientPlan
    onAction: (label: string) => void // clique no botão (por enquanto só mostra um aviso)
}

// Módulo: um plano da tabela. O atual ganha borda e o selo "Seu plano"; os outros, um botão.
export function PlanCard({ plan, current, onAction }: PlanCardProps) {
    const action = planAction(plan, current)
    return (
        <article className={action ? 'card card-pad plan' : 'card card-pad plan current'}>
            <div className="row" style={{ justifyContent: 'space-between' }}>
                <h3 className="h2" style={{ color: 'var(--text)' }}>
                    {plan.name}
                </h3>
                {!action && <span className="badge info">Seu plano</span>}
            </div>
            <div className="stack" style={{ gap: 4 }}>
                <p className="plan-price">{priceLabel(plan)}</p>
                <p className="muted small">{plan.tagline}</p>
            </div>
            <ul className="plan-features">
                {plan.features.map((f) => (
                    <li key={f}>
                        <Icon name="check" size={14} />
                        {f}
                    </li>
                ))}
            </ul>
            {action && (
                <button className="btn plan-action" type="button" onClick={() => onAction(action)}>
                    {action}
                </button>
            )}
        </article>
    )
}
