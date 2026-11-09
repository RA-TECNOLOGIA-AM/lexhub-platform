import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { useAuth } from './contexts/auth-context.ts'
import { AuthProvider } from './contexts/AuthProvider.tsx'
import { RequireAuth } from './components/auth/RequireAuth.tsx'
import { AppLayout } from './components/layout/AppLayout.tsx'
import { DashboardPage } from './pages/dashboards/DashboardPage.tsx'
import { HubPage } from './pages/dashboards/HubPage.tsx'
import { LoginPage } from './pages/LoginPage.tsx'
import { NAV_SECTIONS } from './navigation.ts'
import { ComingSoonPage } from './pages/ComingSoonPage.tsx'
import type { ReactNode } from 'react'
import { MembersPage } from './pages/admin/members/MembersPage.tsx'
import { BillingPage } from './pages/admin/billing/BillingPage.tsx'

// Páginas do menu que já têm conteúdo; as outras abrem a página-base (ComingSoonPage).
const PAGES: Record<string, ReactNode> = {
    membros: <MembersPage />,
    plano: <BillingPage />,
}

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
                            <Route path="/:org/dashboards" element={<HubPage />} />
                            <Route path="/:org/:unit/dashboards/:dashboardKey" element={<DashboardPage />} />
                            {/* Páginas do menu (exceto Dashboards, que já tem as rotas acima). */}
                            {NAV_SECTIONS.flatMap((s) => s.items)
                                .filter((item) => item.key !== 'dashboards')
                                .map((item) => (
                                    <Route
                                        key={item.key}
                                        path={item.route}
                                        element={PAGES[item.key] ?? <ComingSoonPage item={item} />}
                                    />
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
