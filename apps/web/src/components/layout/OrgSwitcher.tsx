import { useRef, useState } from 'react'
import { matchPath, useLocation, useSearchParams } from 'react-router'
import { PageTransitionLink } from '../page_transition/PageTransitionLink.tsx'
import { orgInitials } from '../../lib/orgs.ts'
import {
    hubUnit,
    rememberUnit,
    rememberedUnit,
    sourcesUnit,
    unitChoices,
    unitsWithDashboards,
} from '../../lib/activeUnit.ts'
import { unitLogo, unitName } from '../../lib/units.ts'
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
    onOpen?: () => void // ao abrir a lista (ex.: expandir a barra lateral recolhida, onde a lista não cabe)
}

const DASHBOARD_ROUTE = '/:org/:unit/dashboards/:dashboardKey'

// A logo da unidade na lista; sem logo, um espaço do mesmo tamanho (se reserve) ou nada. Decorativa: o nome vem ao lado.
function UnitLogo({ src, reserve }: { src: string | null; reserve: boolean }) {
    if (src) return <img className="org-unit-logo" src={src} alt="" aria-hidden="true" width={30} height={30} />
    return reserve ? <span className="org-unit-logo is-empty" aria-hidden="true" /> : null
}

type UnitLinkProps = {
    to: string
    label: string
    logo: string | null
    reserve: boolean
    current?: boolean
    onClick: () => void
}

// Uma linha do menu: logo, nome e o check da unidade atual.
function UnitLink({ to, label, logo, reserve, current = false, onClick }: UnitLinkProps) {
    return (
        <PageTransitionLink className="nav" to={to} aria-current={current ? 'true' : undefined} onClick={onClick}>
            <UnitLogo src={logo} reserve={reserve} />
            <span className="org-text">
                <span>{label}</span>
            </span>
            {current && (
                <span role="img" aria-label="Unidade atual" style={{ display: 'inline-flex' }}>
                    <Icon name="check" size={16} />
                </span>
            )}
        </PageTransitionLink>
    )
}

// Módulo: o seletor da barra lateral: organização + unidade. Trocar é só navegar (a URL manda).
// - Num dashboard: as unidades em que ele está liberado; trocar abre o mesmo dashboard na outra unidade.
// - Em Unidades e fontes: todas as unidades, sem "Todas"; trocar mostra as fontes da outra unidade.
// - No resto: "Todas as unidades" (se vê mais de uma) + cada unidade; escolher leva ao hub filtrado.
// - Várias organizações (Owner/Dev da LexGroup entram em todos os clientes): cada uma é uma linha; o nome leva
//   a todas as unidades dela e a seta mostra/esconde as unidades (a atual já abre aberta).
// - A escolha fica lembrada na sessão (lib/activeUnit.ts). Uma unidade e uma organização só: travado.
export function OrgSwitcher({ current, orgs, units, canCreate, onNavigate, onOpen }: OrgSwitcherProps) {
    const [open, setOpen] = useState(false)
    // Várias organizações: quais estão abertas (a atual abre sozinha) e as unidades buscadas ao abrir
    // uma que veio sem a lista (API antiga): undefined = ainda não buscou, null = buscando, 'erro' = falhou.
    const [expanded, setExpanded] = useState<Set<string>>(() => new Set([current.slug]))
    const [fetched, setFetched] = useState<Record<string, Unit[] | null | 'erro'>>({})
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
    // Em Unidades e fontes: todas as unidades (as sem dashboard também, ex.: Escritório de Teste), sem "Todas";
    // a tela mostra só as fontes da unidade escolhida aqui.
    const sourcesRoute = `/${current.slug}/admin/unidades`
    const onSources = pathname === sourcesRoute
    const unit = onDashboard
        ? (onDashboard.params.unit ?? null)
        : onSources
          ? sourcesUnit(
                params.get('unidade'),
                rememberedUnit(current.slug),
                units.map((u) => u.code),
            )
          : hubUnit(onHub ? params.get('unidade') : null, rememberedUnit(current.slug), visibleUnits)
    const choices = onSources
        ? units.map((u) => ({ code: u.code, label: u.name }))
        : unitChoices(visibleUnits, dashboardUnits)
    const locked = choices.length <= 1 && orgs.length <= 1 && !canCreate

    // Para onde leva cada unidade.
    const hrefOf = (code: string | null) =>
        onSources && code
            ? `${sourcesRoute}?unidade=${code}`
            : dashboardKey && code
              ? `/${current.slug}/${code}/dashboards/${dashboardKey}${search}`
              : `/${current.slug}/dashboards${code ? `?unidade=${code}` : ''}`

    // Organização (code null = todas as unidades) ou unidade de outra organização: a mesma tela lá
    // (Unidades e fontes, que abre na primeira unidade, ou o hub filtrado).
    const otherHref = (slug: string, code: string | null) =>
        onSources
            ? `/${slug}/admin/unidades${code ? `?unidade=${code}` : ''}`
            : `/${slug}/dashboards${code ? `?unidade=${code}` : ''}`

    // Se alguma unidade tem logo, as que não têm ("Todas as unidades") ganham um espaço vazio: os nomes alinham.
    const anyLogo = choices.some((c) => unitLogo(c.code))

    // Abre/fecha uma organização. Sem a lista de unidades no "me", busca o "me" dela (Owner/Dev da LexGroup
    // é membro de todo cliente, então a API responde).
    function toggleOrg(o: Org) {
        const next = new Set(expanded)
        if (next.has(o.slug)) next.delete(o.slug)
        else next.add(o.slug)
        setExpanded(next)
        if (!o.units && fetched[o.slug] === undefined) {
            setFetched((f) => ({ ...f, [o.slug]: null }))
            dataClient
                .getMe(o.slug)
                .then((me) => setFetched((f) => ({ ...f, [o.slug]: me.units })))
                .catch(() => setFetched((f) => ({ ...f, [o.slug]: 'erro' })))
        }
    }

    function choose(slug: string, code: string | null) {
        rememberUnit(slug, code)
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
                title={`${current.name}, ${unit ? unitName(unit, units) : 'Todas as unidades'}`}
                onClick={() => {
                    if (!open) {
                        onOpen?.()
                        setExpanded(new Set([current.slug])) // abre sempre com a organização atual aberta
                    }
                    setOpen(!open)
                }}
            >
                {label}
                <Icon name="chevrons" size={16} />
            </button>
            {open && (
                <div id="org-menu" className="org-menu">
                    {/* Uma organização: "Unidades" e a lista. Várias (Owner/Dev da LexGroup veem todas): o nome
                        da organização é o "todas as unidades" dela, seguido de cada unidade; clicar numa unidade
                        de outra organização abre a mesma tela lá. */}
                    {orgs.length > 1
                        ? orgs.map((o) => {
                              const mine = o.slug === current.slug
                              const isOpen = expanded.has(o.slug)
                              const other = o.units ?? fetched[o.slug]
                              const list = mine
                                  ? choices.filter((c) => c.code !== null)
                                  : Array.isArray(other)
                                    ? other.map((u) => ({ code: u.code, label: u.name }))
                                    : []
                              const groupId = `org-units-${o.slug}`
                              return (
                                  <div key={o.slug} className="org-menu-group">
                                      <div className="org-menu-head">
                                          {/* O nome leva a todas as unidades da organização; a seta mostra as unidades. */}
                                          <PageTransitionLink
                                              className="nav org-menu-org"
                                              to={otherHref(o.slug, null)}
                                              aria-current={mine && unit === null ? 'true' : undefined}
                                              onClick={() => choose(o.slug, null)}
                                          >
                                              <span className="org-text">
                                                  <span>{o.name}</span>
                                              </span>
                                              {mine && unit === null && (
                                                  <span
                                                      role="img"
                                                      aria-label="Todas as unidades"
                                                      style={{ display: 'inline-flex' }}
                                                  >
                                                      <Icon name="check" size={16} />
                                                  </span>
                                              )}
                                          </PageTransitionLink>
                                          <button
                                              type="button"
                                              className="org-menu-toggle"
                                              aria-expanded={isOpen}
                                              aria-controls={groupId}
                                              aria-label={`${isOpen ? 'Esconder' : 'Mostrar'} as unidades de ${o.name}`}
                                              onClick={() => toggleOrg(o)}
                                          >
                                              <Icon name={isOpen ? 'chevron-up' : 'chevron-down'} size={16} />
                                          </button>
                                      </div>
                                      {isOpen && (
                                          <div id={groupId} className="org-menu-units">
                                              {!mine && other === null && (
                                                  <span className="org-menu-note">Carregando unidades…</span>
                                              )}
                                              {!mine && other === 'erro' && (
                                                  <span className="org-menu-note">
                                                      Não deu para carregar as unidades.
                                                  </span>
                                              )}
                                              {Array.isArray(other) || mine
                                                  ? list.length === 0 && (
                                                        <span className="org-menu-note">Nenhuma unidade</span>
                                                    )
                                                  : null}
                                              {list.map((c) => (
                                                  <UnitLink
                                                      key={c.code ?? 'todas'}
                                                      to={mine ? hrefOf(c.code) : otherHref(o.slug, c.code)}
                                                      label={c.label}
                                                      logo={unitLogo(c.code)}
                                                      reserve={anyLogo}
                                                      current={mine && c.code === unit}
                                                      onClick={() => choose(o.slug, c.code)}
                                                  />
                                              ))}
                                          </div>
                                      )}
                                  </div>
                              )
                          })
                        : choices.length > 0 && (
                              <>
                                  <span className="org-menu-label">Unidades</span>
                                  {choices.map((c) => (
                                      <UnitLink
                                          key={c.code ?? 'todas'}
                                          to={hrefOf(c.code)}
                                          label={c.label}
                                          logo={unitLogo(c.code)}
                                          reserve={anyLogo}
                                          current={c.code === unit}
                                          onClick={() => choose(current.slug, c.code)}
                                      />
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
