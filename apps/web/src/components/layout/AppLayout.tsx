import { useRef, useState } from 'react'
import { Outlet, useLocation } from 'react-router'
import { useAuth } from '../../contexts/auth-context.ts'
import { Icon } from '../ui/Icon.tsx'
import { NotificationsBell } from './NotificationsBell.tsx'
import { OrgSwitcher } from './OrgSwitcher.tsx'
import { SearchBox } from './SearchBox.tsx'
import { TopbarSlotContext } from './topbar-slot.ts'
import { activeItem, menuPermissions, NAV_SECTIONS, pathOf, visibleItems } from '../../navigation.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { useDismiss } from '../../hooks/useDismiss.ts'
import { usePendingRequests } from '../../hooks/usePendingRequests.ts'
import { dataClient } from '../../services/client.ts'
import { env } from '../../services/env.ts'
import { PageTransitionLink } from '../page_transition/PageTransitionLink.tsx'

export function AppLayout() {
    const [menuOpen, setMenuOpen] = useState(false)
    // Espaço da topbar que uma página pode ocupar (ex.: o Período de um dashboard). Ver TopbarSlot.tsx.
    const [topbarSlot, setTopbarSlot] = useState<HTMLElement | null>(null)
    const menuButton = useRef<HTMLButtonElement>(null)
    const { pathname } = useLocation()
    const { me, signOut } = useAuth()
    // Selo de pedidos de acesso pendentes: só a equipe RA busca.
    const pending = usePendingRequests(!!me?.user.platform_staff)
    // O que a pessoa gere nesta organização: esconde Acesso de Colaborador/Leitor.
    // Se a consulta falhar, o menu mostra tudo (ver menuPermissions): a página já protege sozinha.
    const orgSlug = me?.org.slug ?? ''
    const permsQuery = useAsync(
        () => (orgSlug ? dataClient.getMyAdminPermissions(orgSlug) : Promise.resolve(null)),
        [orgSlug],
    )
    const perms = menuPermissions(permsQuery.data ?? null, permsQuery.error)

    // Página atual: marca o item do menu e monta o breadcrumb ("Administração / Membros").
    const current = me ? activeItem(pathname, me.org.slug) : null
    const dashboardKey = pathname.split('/dashboards/')[1]
    const crumb = [current?.section.title, current?.item.label, dashboardKey].filter(Boolean).join(' / ')

    // Menu do celular: fecha com Esc (foco volta ao botão) ou clicando fora da barra lateral.
    useDismiss({
        open: menuOpen,
        onClose: () => setMenuOpen(false),
        isInside: (target) => !!target.closest('.side, .menu-btn'),
        returnFocus: menuButton,
    })

    // O <RequireAuth> só deixa chegar aqui com alguém logado; o if é para o TypeScript.
    // Fica depois de todos os hooks (regra dos hooks: mesma ordem em toda renderização).
    if (!me) return null
    const { org, user } = me

    const closeMenu = () => setMenuOpen(false)

    return (
        <div className="app" data-menu={menuOpen ? 'open' : undefined}>
            <aside className="side" aria-label="Navegação principal">
                <div className="brand">
                    <span className="brand-mark">LH</span>
                    <span>LexHub</span>
                </div>
                <OrgSwitcher
                    current={org}
                    orgs={me.orgs}
                    units={me.units}
                    canCreate={user.platform_staff}
                    onNavigate={closeMenu}
                />

                {NAV_SECTIONS.filter((section) => !section.platformOnly || user.platform_staff).map((section) => (
                    <div key={section.title} className="stack" style={{ gap: 2 }}>
                        <span className="side-label">{section.title}</span>
                        {visibleItems(section, perms).map((item) => (
                            <PageTransitionLink
                                key={item.key}
                                className="nav"
                                to={pathOf(item, org.slug)}
                                aria-current={current?.item.key === item.key ? 'page' : undefined}
                                onClick={closeMenu}
                            >
                                <Icon name={item.icon} />
                                {item.label}
                                {item.badge === 'access-requests' && pending > 0 && (
                                    <span className="count" aria-label={`${pending} pendentes`}>
                                        {pending}
                                    </span>
                                )}
                            </PageTransitionLink>
                        ))}
                    </div>
                ))}

                <div className="side-user">
                    <span className="av">{user.initials}</span>
                    <span>
                        <span className="name">{user.name}</span>
                        <span className="sub">{user.role_label}</span>
                    </span>
                    {/* Sair só apaga a sessão; o <RequireAuth> é quem manda para o /login. */}
                    <button
                        className="nav"
                        type="button"
                        aria-label="Sair"
                        style={{ width: 'auto', marginLeft: 'auto', padding: 8 }}
                        onClick={() => signOut()}
                    >
                        <Icon name="logout" />
                    </button>
                </div>
            </aside>

            <div className="main">
                <header className="topbar">
                    <button
                        ref={menuButton}
                        className="iconbtn menu-btn"
                        type="button"
                        aria-label="Abrir menu"
                        aria-expanded={menuOpen}
                        onClick={() => setMenuOpen((open) => !open)}
                    >
                        <Icon name="menu" />
                    </button>
                    <div className="crumb">
                        <span className="small muted">
                            {org.name} / {crumb}
                        </span>
                        <span className="path">lexhub.app{pathname}</span>
                    </div>
                    {/* Só no modo mock: em modo api os dados vêm da API V2. */}
                    {env.dataSource === 'mock' && <span className="badge warn">Dados fictícios</span>}
                    {/* A página atual pode ocupar este espaço (ex.: Período do dashboard). */}
                    <div className="topbar-slot" ref={setTopbarSlot} />
                    <SearchBox org={org.slug} />
                    <NotificationsBell staff={user.platform_staff} pending={pending} onNavigate={closeMenu} />
                </header>

                <main className="content">
                    <TopbarSlotContext value={topbarSlot}>
                        <Outlet />
                    </TopbarSlotContext>
                </main>
            </div>
        </div>
    )
}
