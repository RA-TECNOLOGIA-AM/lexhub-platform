import { PageTransitionLink } from '../page_transition/PageTransitionLink.tsx'
import type { DashboardSummary } from '../../types/index.ts'
import { isDisabled } from '../../lib/dashboardSwitch.ts'
import { dashboardHref } from '../../lib/orgDashboard.ts'
import { DashboardSwitchMenu } from './DashboardSwitchMenu.tsx'
import { Freshness } from './Freshness.tsx'
import { Icon } from '../ui/Icon.tsx'

type DashboardCardProps = {
    org: string
    unit: string // em qual unidade o cartão abre o dashboard
    dashboard: DashboardSummary
    favorite: boolean
    // O card só avisa o clique; quem guarda é quem usa o card. Sem ele (modo suporte, só leitura): sem estrela.
    onToggleFavorite?: () => void
    showUnits?: boolean // etiquetas das unidades (só em "Todas as unidades"; com uma escolhida, não repete o filtro)
    // Só o Desenvolvedor (dashboard.can_toggle): liga/desliga numa unidade. Quem usa o card grava e atualiza a tela.
    onSetEnabled?: (unit: string, enabled: boolean) => Promise<void>
}

// O card inteiro é clicável pelo link do título (o ::after dele cobre o card); estrela e menu ficam por cima.
export function DashboardCard({
    org,
    unit,
    dashboard,
    favorite,
    onToggleFavorite,
    showUnits = true,
    onSetEnabled,
}: DashboardCardProps) {
    const disabledUnits = dashboard.disabled_units ?? []
    // Desligado na unidade escolhida (ou em todas, sem unidade escolhida): só o Dev chega a ver este card.
    const off = isDisabled(dashboard, showUnits ? null : unit)
    // O nome deixa a View Transition reconhecer o card ao trocar de seção (por isso cada card aparece uma vez só).
    return (
        <article
            className={off ? 'card dcard is-off' : 'card dcard'}
            style={{ viewTransitionName: `card-${dashboard.key}` }}
        >
            <span className="dcard-head">
                <PageTransitionLink className="title dcard-link" to={dashboardHref(org, unit, dashboard)}>
                    {dashboard.title}
                </PageTransitionLink>
                <span className="dcard-actions">
                    {onToggleFavorite && (
                        <button
                            type="button"
                            className="fav-btn"
                            aria-label={`Favoritar ${dashboard.title}`}
                            aria-pressed={favorite}
                            onClick={onToggleFavorite}
                        >
                            <Icon name="star" />
                        </button>
                    )}
                    {dashboard.can_toggle && onSetEnabled && (
                        <DashboardSwitchMenu
                            title={dashboard.title}
                            units={dashboard.units}
                            disabledUnits={disabledUnits}
                            onChange={onSetEnabled}
                        />
                    )}
                </span>
            </span>
            <span className="desc">{dashboard.desc}</span>
            {off && <span className="badge neutral dcard-off">Desativado · só você vê</span>}
            {showUnits && (
                <span className="tags">
                    {dashboard.units.map((u) => {
                        const unitOff = disabledUnits.includes(u)
                        return (
                            <span
                                key={u}
                                className={unitOff ? 'tag off' : 'tag'}
                                title={unitOff ? 'Desativado nesta unidade' : undefined}
                            >
                                {u.replace('_', ' ')}
                            </span>
                        )
                    })}
                </span>
            )}
            <Freshness
                syncedAt={dashboard.synced_at}
                source={dashboard.source}
                maxDelayMin={dashboard.max_delay_min}
                disabled={dashboard.source_disabled}
            />
        </article>
    )
}
