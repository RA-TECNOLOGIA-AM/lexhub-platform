import { Link } from 'react-router'
import { useAuth } from '../auth/auth-context.ts'
import type { DashboardSummary, Meta } from '../data/types.ts'
import { Freshness } from './Freshness.tsx'
import { Icon } from './Icon.tsx'
import { PillGroup } from './PillGroup.tsx'

type DashboardHeaderProps = {
    org: string
    dashboard: DashboardSummary // item do catálogo (título, unidades liberadas, limite de atraso)
    meta: Meta // de onde e de quando são os dados desta resposta
}

// Cabeçalho comum dos dashboards: voltar, título com a unidade, selo de atualização e troca de unidade.
export function DashboardHeader({ org, dashboard, meta }: DashboardHeaderProps) {
    const { me } = useAuth()
    // Só as unidades em que este dashboard está liberado; o nome vem do usuário logado.
    const units = (me?.units ?? []).filter((u) => dashboard.units.includes(u.code))
    const current = units.find((u) => u.code === meta.unit)

    return (
        <section className="stack">
            <div className="stack" style={{ gap: 4 }}>
                <Link to={`/${org}/dashboards`} className="back-link">
                    <Icon name="arrowLeft" size={16} />
                    Dashboards
                </Link>
                <h1 className="h1">
                    {dashboard.title}
                    {current && ` · ${current.name}`}
                </h1>
                <Freshness syncedAt={meta.synced_at} source={meta.source} maxDelayMin={dashboard.max_delay_min} />
            </div>

            {units.length > 1 && (
                <PillGroup
                    label="Unidade"
                    items={units.map((u) => ({
                        id: u.code,
                        label: u.name,
                        to: `/${org}/${u.code}/dashboards/${dashboard.key}`,
                        active: u.code === meta.unit,
                    }))}
                />
            )}
        </section>
    )
}
