import { Link } from 'react-router'
import type { DashboardSummary } from '../../types/index.ts'
import { Freshness } from './Freshness.tsx'
import { Icon } from '../ui/Icon.tsx'

type DashboardCardProps = {
    org: string
    unit: string // em qual unidade o cartão abre o dashboard
    dashboard: DashboardSummary
    favorite: boolean
    onToggleFavorite: () => void // o card só avisa o clique; quem guarda é quem usa o card
}

// O card inteiro é clicável pelo link do título (o ::after dele cobre o card); a estrela fica por cima.
export function DashboardCard({ org, unit, dashboard, favorite, onToggleFavorite }: DashboardCardProps) {
    // O nome deixa a View Transition reconhecer o card ao trocar de seção (por isso cada card aparece uma vez só).
    return (
        <article className="card dcard" style={{ viewTransitionName: `card-${dashboard.key}` }}>
            <span className="dcard-head">
                <Link className="title dcard-link" to={`/${org}/${unit}/dashboards/${dashboard.key}`}>
                    {dashboard.title}
                </Link>
                <button
                    type="button"
                    className="fav-btn"
                    aria-label={`Favoritar ${dashboard.title}`}
                    aria-pressed={favorite}
                    onClick={onToggleFavorite}
                >
                    <Icon name="star" />
                </button>
            </span>
            <span className="desc">{dashboard.desc}</span>
            <span className="tags">
                {dashboard.units.map((u) => (
                    <span key={u} className="tag">
                        {u.replace('_', ' ')}
                    </span>
                ))}
            </span>
            <Freshness syncedAt={dashboard.synced_at} source={dashboard.source} maxDelayMin={dashboard.max_delay_min} />
        </article>
    )
}
