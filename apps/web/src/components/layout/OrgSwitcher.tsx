import { useRef, useState } from 'react'
import { matchPath, useLocation, useSearchParams } from 'react-router'
import { PageTransitionLink } from '../page_transition/PageTransitionLink.tsx'
import { orgInitials } from '../../lib/orgs.ts'
import { hubUnit, rememberUnit, rememberedUnit, unitChoices, unitsWithDashboards } from '../../lib/activeUnit.ts'
import { unitName } from '../../lib/units.ts'
import type { Org, Unit } from '../../types/index.ts'
import { Icon } from '../ui/Icon.tsx'
import { useDismiss } from '../../hooks/useDismiss.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { dataClient } from '../../services/client.ts'

type OrgSwitcherProps = {
    current: Org
    orgs: Org[] // as organizações da pessoa
    units: Unit[] // as unidades que a pessoa vê na organização atual
    canCreate: boolean // equipe RA: mostra "Criar organização" (leva ao console da plataforma)
    onNavigate: () => void // ao escolher um item (ex.: fechar o menu do celular)
}

const DASHBOARD_ROUTE = '/:org/:unit/dashboards/:dashboardKey'

// Módulo: o seletor da barra lateral: organização + unidade. Trocar é só navegar (a URL manda).
// - Num dashboard: as unidades em que ele está liberado; trocar abre o mesmo dashboard na outra unidade.
// - No resto: "Todas as unidades" (se vê mais de uma) + cada unidade; escolher leva ao hub filtrado.
// - A escolha fica lembrada na sessão (lib/activeUnit.ts). Uma unidade e uma organização só: travado.
export function OrgSwitcher({ current, orgs, units, canCreate, onNavigate }: OrgSwitcherProps) {
    const [open, setOpen] = useState(false)
    const root = useRef<HTMLDivElement>(null)
    const button = useRef<HTMLButtonElement>(null)
    const { pathname, search } = useLocation()
    const [params] = useSearchParams()

    useDismiss({
        open,
        onClose: () => setOpen(false),
        isInside: (target) => !!root.current?.contains(target),
        returnFocus: button,
    })

    const onDashboard = matchPath(DASHBOARD_ROUTE, pathname)
    const dashboardKey = onDashboard?.params.dashboardKey ?? null
    // O catálogo (já em memória na sessão: não espera a API) diz quais unidades têm dashboards
    // e, num dashboard, em quais unidades ele está liberado.
    const { data: catalog } = useAsync(() => dataClient.listDashboards(current.slug), [current.slug])
    const visibleUnits = unitsWithDashboards(units, catalog?.available ?? null)
    const dashboardUnits = dashboardKey
        ? (catalog?.available.find((d) => d.key === dashboardKey)?.units ?? [onDashboard?.params.unit ?? ''])
        : null

    const onHub = pathname === `/${current.slug}/dashboards`
    const unit = onDashboard
        ? (onDashboard.params.unit ?? null)
        : hubUnit(onHub ? params.get('unidade') : null, rememberedUnit(current.slug), visibleUnits)
    const choices = unitChoices(visibleUnits, dashboardUnits)
    const locked = choices.length <= 1 && orgs.length <= 1 && !canCreate

    // Para onde leva cada unidade.
    const hrefOf = (code: string | null) =>
        dashboardKey && code
            ? `/${current.slug}/${code}/dashboards/${dashboardKey}${search}`
            : `/${current.slug}/dashboards${code ? `?unidade=${code}` : ''}`

    function choose(code: string | null) {
        rememberUnit(current.slug, code)
        setOpen(false)
        onNavigate()
    }

    const label = (
        <>
            <span className="org-mark">{orgInitials(current.name)}</span>
            <span className="org-text">
                <span className="org-name">{current.name}</span>
                <span className="org-sub">{unit ? unitName(unit, units) : 'Todas as unidades'}</span>
            </span>
        </>
    )

    if (locked) {
        return (
            <div className="org-switch">
                <div className="org" aria-label={`${current.name}, ${unit ? unitName(unit, units) : ''}`}>
                    {label}
                </div>
            </div>
        )
    }

    return (
        <div className="org-switch" ref={root}>
            <button
                ref={button}
                className="org"
                type="button"
                aria-expanded={open}
                aria-controls="org-menu"
                onClick={() => setOpen((o) => !o)}
            >
                {label}
                <Icon name="chevrons" size={16} />
            </button>
            {open && (
                <div id="org-menu" className="org-menu">
                    {choices.length > 0 && <span className="org-menu-label">Unidades</span>}
                    {choices.map((c) => (
                        <PageTransitionLink
                            key={c.code ?? 'todas'}
                            className="nav"
                            to={hrefOf(c.code)}
                            aria-current={c.code === unit ? 'true' : undefined}
                            onClick={() => choose(c.code)}
                        >
                            <span className="org-text">
                                <span>{c.label}</span>
                            </span>
                            {c.code === unit && (
                                <span role="img" aria-label="Unidade atual" style={{ display: 'inline-flex' }}>
                                    <Icon name="check" size={16} />
                                </span>
                            )}
                        </PageTransitionLink>
                    ))}
                    {orgs.length > 1 && (
                        <>
                            <span className="org-menu-label">Organizações</span>
                            {orgs.map((o) => (
                                <PageTransitionLink
                                    key={o.slug}
                                    className="nav"
                                    to={`/${o.slug}/dashboards`}
                                    aria-current={o.slug === current.slug ? 'true' : undefined}
                                    onClick={() => {
                                        setOpen(false)
                                        onNavigate()
                                    }}
                                >
                                    <span className="org-text">
                                        <span>{o.name}</span>
                                        <span className="org-sub">{o.sub}</span>
                                    </span>
                                    {o.slug === current.slug && (
                                        <span
                                            role="img"
                                            aria-label="Organização atual"
                                            style={{ display: 'inline-flex' }}
                                        >
                                            <Icon name="check" size={16} />
                                        </span>
                                    )}
                                </PageTransitionLink>
                            ))}
                        </>
                    )}
                    {canCreate && (
                        <PageTransitionLink
                            className="nav"
                            to="/plataforma/clientes"
                            onClick={() => {
                                setOpen(false)
                                onNavigate()
                            }}
                        >
                            <Icon name="plus" size={16} />
                            Criar organização
                        </PageTransitionLink>
                    )}
                </div>
            )}
        </div>
    )
}
