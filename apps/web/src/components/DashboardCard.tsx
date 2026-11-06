import { Link } from 'react-router'
import type { DashboardSummary } from '../data/types.ts'
import { Freshness } from './Freshness.tsx'

type DashboardCardProps = {
    org: string
    unit: string // em qual unidade o cartão abre o dashboard
    dashboard: DashboardSummary
}

export function DashboardCard({ org, unit, dashboard }: DashboardCardProps) {
    return (
        <Link className="card dcard" to={`/${org}/${unit}/dashboards/${dashboard.key}`}>
            <span className="title">{dashboard.title}</span>
            <span className="desc">{dashboard.desc}</span>
            <span className="tags">
                {dashboard.units.map((u) => (
                    <span key={u} className="tag">
                        {u.replace('_', ' ')}
                    </span>
                ))}
            </span>
            <Freshness syncedAt={dashboard.synced_at} source={dashboard.source} maxDelayMin={dashboard.max_delay_min} />
        </Link>
    )
}
