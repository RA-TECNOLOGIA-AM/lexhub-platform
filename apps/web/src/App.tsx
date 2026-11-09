import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { useAuth } from './contexts/auth-context.ts'
import { AuthProvider } from './contexts/AuthProvider.tsx'
import { RequireAuth } from './components/auth/RequireAuth.tsx'
import { OrgScope } from './components/auth/OrgScope.tsx'
import { AppLayout } from './components/layout/AppLayout.tsx'
import { DashboardPage } from './pages/dashboards/DashboardPage.tsx'
import { HubPage } from './pages/dashboards/HubPage.tsx'
import { LoginPage } from './pages/LoginPage.tsx'
import { NAV_SECTIONS, type NavItem } from './navigation.ts'
import { ComingSoonPage } from './pages/ComingSoonPage.tsx'
import type { ReactNode } from 'react'
import { MembersPage } from './pages/admin/members/MembersPage.tsx'
import { BillingPage } from './pages/admin/billing/BillingPage.tsx'
import { AccessPage } from './pages/admin/access/AccessPage.tsx'
import { AuditPage } from './pages/admin/audit/AuditPage.tsx'
import { ClientsPage } from './pages/platform/clients/ClientsPage.tsx'

// Páginas do menu que já têm conteúdo; as outras abrem a página-base (ComingSoonPage).
const PAGES: Record<string, ReactNode> = {
    membros: <MembersPage />,
    plano: <BillingPage />,
    acesso: <AccessPage />,
    auditoria: <AuditPage />,
    clientes: <ClientsPage />,
}

// Páginas do menu (exceto Dashboards, que tem rotas próprias). As de organização ('/:org/admin/...')
// ficam dentro do OrgScope com o caminho relativo; as da plataforma ('/plataforma/...') ficam fora.
const ORG_PREFIX = '/:org/'
const MENU_ITEMS = NAV_SECTIONS.flatMap((s) => s.items).filter((item) => item.key !== 'dashboards')
const pageOf = (item: NavItem) => PAGES[item.key] ?? <ComingSoonPage item={item} />

// Endereço desconhecido: vai para o hub da organização de quem está logado.
function GoToHub() {
    const { me } = useAuth()
    return <Navigate to={`/${me?.org.slug}/dashboards`} replace />
}

function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <Routes>
                    <Route path="/login" element={<LoginPage />} />
                    <Route element={<RequireAuth />}>
                        <Route element={<AppLayout />}>
                            {/* Tudo de uma organização: o OrgScope garante que a ativa é a da URL. */}
                            <Route path="/:org" element={<OrgScope />}>
                                <Route index element={<Navigate to="dashboards" replace />} />
                                <Route path="dashboards" element={<HubPage />} />
                                <Route path=":unit/dashboards/:dashboardKey" element={<DashboardPage />} />
                                {MENU_ITEMS.filter((item) => item.route.startsWith(ORG_PREFIX)).map((item) => (
                                    <Route
                                        key={item.key}
                                        path={item.route.slice(ORG_PREFIX.length)}
                                        element={pageOf(item)}
                                    />
                                ))}
                            </Route>
                            {MENU_ITEMS.filter((item) => !item.route.startsWith(ORG_PREFIX)).map((item) => (
                                <Route key={item.key} path={item.route} element={pageOf(item)} />
                            ))}
                        </Route>
                        <Route path="*" element={<GoToHub />} />
                    </Route>
                </Routes>
            </AuthProvider>
        </BrowserRouter>
    )
}

export default App
