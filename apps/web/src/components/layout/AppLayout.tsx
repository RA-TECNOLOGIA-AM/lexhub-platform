import { useRef, useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router'
import { useAuth } from '../../contexts/auth-context.ts'
import { Icon } from '../ui/Icon.tsx'
import { OrgSwitcher } from './OrgSwitcher.tsx'
import { SearchBox } from './SearchBox.tsx'
import { activeItem, NAV_SECTIONS, pathOf } from '../../navigation.ts'
import { useDismiss } from '../../hooks/useDismiss.ts'

export function AppLayout() {
    const [menuOpen, setMenuOpen] = useState(false)
    const menuButton = useRef<HTMLButtonElement>(null)
    const { pathname } = useLocation()
    const { me, signOut } = useAuth()

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
                <OrgSwitcher current={org} orgs={me.orgs} canCreate={user.platformStaff} onNavigate={closeMenu} />

                {NAV_SECTIONS.filter((section) => !section.platformOnly || user.platformStaff).map((section) => (
                    <div key={section.title} className="stack" style={{ gap: 2 }}>
                        <span className="side-label">{section.title}</span>
                        {section.items.map((item) => (
                            <Link
                                key={item.key}
                                className="nav"
                                to={pathOf(item, org.slug)}
                                aria-current={current?.item.key === item.key ? 'page' : undefined}
                                onClick={closeMenu}
                            >
                                <Icon name={item.icon} />
                                {item.label}
                            </Link>
                        ))}
                    </div>
                ))}

                <div className="side-user">
                    <span className="av">{user.initials}</span>
                    <span>
                        <span className="name">{user.name}</span>
                        <span className="sub">{user.roleLabel}</span>
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
                    <span className="badge warn">Dados fictícios</span>
                    <SearchBox org={org.slug} />
                    <button className="iconbtn" type="button" aria-label="Notificações">
                        <Icon name="bell" />
                    </button>
                </header>

                <main className="content">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
