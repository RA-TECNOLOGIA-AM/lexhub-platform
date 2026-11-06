import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { useAuth } from './auth/auth-context.ts'
import { AuthProvider } from './auth/AuthProvider.tsx'
import { RequireAuth } from './auth/RequireAuth.tsx'
import { AppLayout } from './components/AppLayout.tsx'
import { DashboardPage } from './pages/DashboardPage.tsx'
import { HubPage } from './pages/HubPage.tsx'
import { LoginPage } from './pages/LoginPage.tsx'

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
                        </Route>
                        <Route path="*" element={<GoToHub />} />
                    </Route>
                </Routes>
            </AuthProvider>
        </BrowserRouter>
    )
}

export default App
