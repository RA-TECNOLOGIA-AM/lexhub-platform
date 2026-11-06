import { useEffect, useRef, useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router'
import { useAuth } from '../auth/auth-context.ts'
import { Icon, type IconName } from './Icon.tsx'

// Administração no MVP: só leitura, ainda "em breve".
const ADMIN_SOON: { label: string; icon: IconName }[] = [
    { label: 'Membros', icon: 'users' },
    { label: 'Acesso', icon: 'key' },
    { label: 'Unidades e fontes', icon: 'db' },
    { label: 'Auditoria', icon: 'history' },
]

export function AppLayout() {
    const [menuOpen, setMenuOpen] = useState(false)
    const menuButton = useRef<HTMLButtonElement>(null)
    const { pathname } = useLocation()
    const { me, signOut } = useAuth()

    // Hub e dashboards ficam todos sob "Dashboards" na barra lateral.
    const inDashboards = pathname.includes('/dashboards')
    const dashboardKey = pathname.split('/dashboards/')[1]
    const crumb = dashboardKey ? `Dashboards / ${dashboardKey}` : 'Dashboards'

    // Menu do celular: fecha com Esc ou clicando fora da barra lateral.
    useEffect(() => {
        if (!menuOpen) return
        function onKey(e: KeyboardEvent) {
            if (e.key === 'Escape') {
                setMenuOpen(false)
                menuButton.current?.focus()
            }
        }
        function onClick(e: MouseEvent) {
            const target = e.target as Element
            if (!target.closest('.side, .menu-btn')) setMenuOpen(false)
        }
        document.addEventListener('keydown', onKey)
        document.addEventListener('click', onClick)
        return () => {
            document.removeEventListener('keydown', onKey)
            document.removeEventListener('click', onClick)
        }
    }, [menuOpen])

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
                <div className="org">
                    <span className="org-mark">LG</span>
                    <span>
                        <span className="org-name">{org.name}</span>
                        <span className="org-sub">{org.sub}</span>
                    </span>
                </div>

                <span className="side-label">Espaço de trabalho</span>
                <Link
                    className="nav"
                    to={`/${org.slug}/dashboards`}
                    aria-current={inDashboards ? 'page' : undefined}
                    onClick={closeMenu}
                >
                    <Icon name="grid" />
                    Dashboards
                </Link>

                <span className="side-label">Administração · somente leitura</span>
                {ADMIN_SOON.map((item) => (
                    <a key={item.label} className="nav" aria-disabled="true" tabIndex={-1}>
                        <Icon name={item.icon} />
                        {item.label}
                        <span className="soon">em breve</span>
                    </a>
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
                    <label className="search">
                        <span className="sr-only">Buscar dashboard</span>
                        <input className="field" type="search" placeholder="Buscar dashboard" />
                        <Icon name="search" size={16} style={{ color: 'var(--text-muted)' }} />
                    </label>
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