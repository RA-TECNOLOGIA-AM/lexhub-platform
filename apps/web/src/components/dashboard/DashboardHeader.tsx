import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router'
import { useAuth } from '../../contexts/auth-context.ts'
import type { DashboardSummary, Meta } from '../../types/index.ts'
import { Freshness } from './Freshness.tsx'
import { Icon } from '../ui/Icon.tsx'
import { PillGroup } from '../ui/PillGroup.tsx'
import { unitName } from '../../lib/units.ts'

type DashboardHeaderProps = {
    org: string
    dashboard: DashboardSummary // item do catálogo (título, unidades liberadas, limite de atraso)
    meta: Meta // de onde e de quando são os dados desta resposta
    actions?: ReactNode // à direita do título (a barra Período · Filtros · Exportar)
}

// Cabeçalho comum dos dashboards: voltar, título com a unidade, selo de atualização, ações e troca de unidade.
export function DashboardHeader({ org, dashboard, meta, actions }: DashboardHeaderProps) {
    const { me } = useAuth()
    const { search } = useLocation() // '?from=...&materia=...': vai junto ao trocar de unidade
    // Só as unidades em que este dashboard está liberado; o nome vem do usuário logado.
    const units = (me?.units ?? []).filter((u) => dashboard.units.includes(u.code))

    return (
        <section className="stack">
            <Link to={`/${org}/dashboards`} className="back-link">
                <Icon name="arrowLeft" size={16} />
                Dashboards
            </Link>
            {/* Mesmo layout das páginas do menu: título à esquerda, ações à direita (quebram no celular). */}
            <div className="page-header">
                <div className="stack" style={{ gap: 4 }}>
                    <h1 className="h1">
                        {dashboard.title} · {unitName(meta.unit, me?.units ?? [])}
                    </h1>
                    <Freshness syncedAt={meta.synced_at} source={meta.source} maxDelayMin={dashboard.max_delay_min} />
                </div>
                {actions && <div className="page-actions">{actions}</div>}
            </div>

            {units.length > 1 && (
                <PillGroup
                    label="Unidade"
                    items={units.map((u) => ({
                        id: u.code,
                        label: u.name,
                        to: `/${org}/${u.code}/dashboards/${dashboard.key}${search}`,
                        active: u.code === meta.unit,
                    }))}
                />
            )}
        </section>
    )
}
