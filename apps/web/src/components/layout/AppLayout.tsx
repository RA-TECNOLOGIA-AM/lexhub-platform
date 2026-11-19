import { Suspense, useRef, useState } from 'react'
import { LoadingState } from '../states/LoadingState.tsx'
import { Link, Outlet, useLocation } from 'react-router'
import { useAuth } from '../../contexts/auth-context.ts'
import { Avatar } from '../ui/Avatar.tsx'
import { Icon } from '../ui/Icon.tsx'
import { NotificationsBell } from './NotificationsBell.tsx'
import { OrgSwitcher } from './OrgSwitcher.tsx'
import { ProfileMenu } from './ProfileMenu.tsx'
import { SearchBox } from './SearchBox.tsx'
import { ThemeToggle } from './ThemeToggle.tsx'
import { FullscreenToggle } from './FullscreenToggle.tsx'
import { SidebarToggle } from './SidebarToggle.tsx'
import { TopbarSlotContext } from './topbar-slot.ts'
import { activeItem, menuPermissions, NAV_SECTIONS, pathOf, visibleItems } from '../../navigation.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { useDismiss } from '../../hooks/useDismiss.ts'
import { useSidebarCollapsed } from '../../hooks/useSidebarCollapsed.ts'
import { usePendingRequests } from '../../hooks/usePendingRequests.ts'
import { dataClient } from '../../services/client.ts'
import { env } from '../../services/env.ts'
import { PageTransitionLink } from '../page_transition/PageTransitionLink.tsx'
import { useTransitionArea } from '../page_transition/useTransitionArea.ts'

function sidebarName(name: string): string {
    const parts = name.trim().split(/\s+/).filter(Boolean)
    const first = parts[0]
    const last = parts[parts.length - 1]
    return parts.length > 2 && first && last ? `${first} ${last}` : name
}

export function AppLayout() {
    const [menuOpen, setMenuOpen] = useState(false)
    // Barra lateral recolhida (só ícones), lembrada no localStorage. Só vale no computador: no celular é gaveta.
    const { collapsed, setCollapsed } = useSidebarCollapsed()
    // Espaços da topbar que uma página pode ocupar (ex.: nome e Período de um dashboard). Ver TopbarSlot.tsx.
    const [topbarStart, setTopbarStart] = useState<HTMLElement | null>(null)
    const [topbarEnd, setTopbarEnd] = useState<HTMLElement | null>(null)
    const menuButton = useRef<HTMLButtonElement>(null)
    const transitionArea = useTransitionArea()
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

    // Página atual: marca o item do menu.
    const current = me ? activeItem(pathname, me.org.slug) : null
    const dashboardKey = pathname.split('/dashboards/')[1]

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
    // Logo da barra lateral: no computador recolhe/expande; no celular (gaveta) fecha o menu.
    const toggleSide = () => {
        if (window.matchMedia('(max-width: 860px)').matches) closeMenu()
        else setCollapsed(!collapsed)
    }

    return (
        <div className="app" data-menu={menuOpen ? 'open' : undefined} data-side={collapsed ? 'collapsed' : undefined}>
            <aside className="side" aria-label="Navegação principal">
                <div className="brand">
                    <SidebarToggle collapsed={collapsed} onToggle={toggleSide} />
                    <span className="brand-name">LexHub</span>
                </div>
                <OrgSwitcher
                    current={org}
                    orgs={me.orgs}
                    units={me.units}
                    canCreate={user.platform_staff}
                    onNavigate={closeMenu}
                    onOpen={() => setCollapsed(false)}
                />

                {/* Só a lista de páginas rola quando não cabe (janela baixa, zoom alto): logo, organização e
                    usuário ficam parados. Antes a barra inteira rolava e parecia subir e descer. */}
                <div className="side-nav">
                    {NAV_SECTIONS.map((section) => ({
                        section,
                        items: visibleItems(section, perms, user.platform_staff),
                    }))
                        .filter(({ items }) => items.length > 0)
                        .map(({ section, items }) => (
                            <div key={section.title} className="stack" style={{ gap: 2 }}>
                                <span className="side-label">{section.title}</span>
                                {items.map((item) => (
                                    <PageTransitionLink
                                        key={item.key}
                                        className="nav"
                                        to={pathOf(item, org.slug)}
                                        aria-current={current?.item.key === item.key ? 'page' : undefined}
                                        title={collapsed ? item.label : undefined}
                                        onClick={closeMenu}
                                    >
                                        <Icon name={item.icon} />
                                        <span className="nav-label">{item.label}</span>
                                        {item.badge === 'access-requests' && pending > 0 && (
                                            <span className="count" aria-label={`${pending} pendentes`}>
                                                {pending}
                                            </span>
                                        )}
                                    </PageTransitionLink>
                                ))}
                            </div>
                        ))}
                </div>

                <div className="side-user">
                    <Avatar user={user} />
                    <span className="side-user-text">
                        <span className="name">{sidebarName(user.name)}</span>
                        <span className="sub">{user.role_label}</span>
                    </span>
                    {/* Conectar uma TV: digitar o código que a TV mostra (/ativar), sem precisar do QR. */}
                    <Link
                        className="nav side-logout side-tv"
                        to="/ativar"
                        aria-label="Conectar uma TV"
                        title="Conectar uma TV"
                        onClick={closeMenu}
                    >
                        <Icon name="qr" />
                    </Link>
                    {/* Sair só apaga a sessão; o <RequireAuth> é quem manda para o /login. */}
                    <button
                        className="nav side-logout"
                        type="button"
                        aria-label="Sair"
                        title="Sair"
                        onClick={() => signOut()}
                    >
                        <Icon name="logout" />
                    </button>
                </div>
            </aside>

            {/* Troca de página: a logo da transição cobre só esta coluna, abaixo da topbar (ver PageTransitionProvider). */}
            <div className="main" ref={transitionArea}>
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
                    {/* Nome da página atual (ex.: dashboard); também empurra o resto da topbar para a direita. */}
                    <div className="topbar-spacer topbar-start" ref={setTopbarStart} />
                    {/* Só no modo mock: em modo api os dados vêm da API V2. */}
                    {env.dataSource === 'mock' && <span className="badge warn">Dados fictícios</span>}
                    {/* A página atual pode ocupar este espaço (ex.: Período do dashboard). */}
                    <div className="topbar-slot" ref={setTopbarEnd} />
                    {/* Busca de dashboards só fora deles (hub, admin...): dentro de um dashboard sai da frente. */}
                    {!dashboardKey && <SearchBox org={org.slug} />}
                    <NotificationsBell staff={user.platform_staff} pending={pending} onNavigate={closeMenu} />
                    <FullscreenToggle />
                    <ThemeToggle />
                    <ProfileMenu user={user} />
                </header>

                <main className="content">
                    <TopbarSlotContext value={{ start: topbarStart, end: topbarEnd }}>
                        {/* Páginas carregadas sob demanda (lazy): o "carregando" fica só no miolo. */}
                        <Suspense fallback={<LoadingState />}>
                            <Outlet />
                        </Suspense>
                    </TopbarSlotContext>
                </main>
            </div>
        </div>
    )
}
