import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { Suspense, type ReactNode } from 'react'
import { useAuth } from './contexts/auth-context.ts'
import { AuthProvider } from './contexts/AuthProvider.tsx'
import { RequireAuth } from './components/auth/RequireAuth.tsx'
import { OrgScope } from './components/auth/OrgScope.tsx'
import { AppLayout } from './components/layout/AppLayout.tsx'
import { LoadingState } from './components/states/LoadingState.tsx'
import { DashboardPage } from './pages/dashboards/DashboardPage.tsx'
import { HubPage } from './pages/dashboards/HubPage.tsx'
import { NAV_SECTIONS, type NavItem } from './navigation.ts'
import { ComingSoonPage } from './pages/ComingSoonPage.tsx'
import { PageTransitionProvider } from './components/page_transition/PageTransitionProvider.tsx'
import { lazyNamed } from './lib/lazyNamed.ts'

// Hub e DashboardPage (a casca; cada dashboard é carregado à parte no registry) ficam no bundle
// inicial: são a 1ª tela de quem entra. O resto só é baixado quando a pessoa abre a página.
const LoginPage = lazyNamed(() => import('./pages/LoginPage.tsx'), 'LoginPage')
const MembersPage = lazyNamed(() => import('./pages/admin/members/MembersPage.tsx'), 'MembersPage')
const BillingPage = lazyNamed(() => import('./pages/admin/billing/BillingPage.tsx'), 'BillingPage')
const AccessPage = lazyNamed(() => import('./pages/admin/access/AccessPage.tsx'), 'AccessPage')
const AuditPage = lazyNamed(() => import('./pages/admin/audit/AuditPage.tsx'), 'AuditPage')
const ClientsPage = lazyNamed(() => import('./pages/platform/clients/ClientsPage.tsx'), 'ClientsPage')
const AccessRequestsPage = lazyNamed(
    () => import('./pages/platform/requests/AccessRequestsPage.tsx'),
    'AccessRequestsPage',
)
const DocumentacaoPage = lazyNamed(() => import('./pages/documentacao/DocumentacaoPage.tsx'), 'DocumentacaoPage')
const DocumentoPage = lazyNamed(() => import('./pages/documentacao/DocumentoPage.tsx'), 'DocumentoPage')
const SourcesPage = lazyNamed(() => import('./pages/admin/sources/SourcesPage.tsx'), 'SourcesPage')

// Páginas do menu que já têm conteúdo; as outras abrem a página-base (ComingSoonPage).
const PAGES: Record<string, ReactNode> = {
    membros: <MembersPage />,
    plano: <BillingPage />,
    acesso: <AccessPage />,
    auditoria: <AuditPage />,
    clientes: <ClientsPage />,
    pedidos: <AccessRequestsPage />,
    documentacao: <DocumentacaoPage />,
    unidades: <SourcesPage />,
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
                <PageTransitionProvider>
                    {/* Só para o que fica fora do AppLayout (ex.: /login); dentro dele, o Suspense do layout
                        segura o miolo e mantém menu e topbar na tela enquanto a página baixa. */}
                    <Suspense fallback={<LoadingState />}>
                        <Routes>
                            <Route path="/login" element={<LoginPage />} />
                            <Route element={<RequireAuth />}>
                                <Route element={<AppLayout />}>
                                    {/* Tudo de uma organização: o OrgScope garante que a ativa é a da URL. */}
                                    <Route path="/:org" element={<OrgScope />}>
                                        <Route index element={<Navigate to="dashboards" replace />} />
                                        <Route path="dashboards" element={<HubPage />} />
                                        <Route path=":unit/dashboards/:dashboardKey" element={<DashboardPage />} />
                                        <Route path="documentacao/:slug" element={<DocumentoPage />} />
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
                    </Suspense>
                </PageTransitionProvider>
            </AuthProvider>
        </BrowserRouter>
    )
}

export default App
