import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { AppLayout } from './components/AppLayout.tsx'
import { DashboardPage } from './pages/DashboardPage.tsx'
import { HubPage } from './pages/HubPage.tsx'
import { LoginPage } from './pages/LoginPage.tsx'

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route element={<AppLayout />}>
                    <Route path="/:org/dashboards" element={<HubPage />} />
                    <Route path="/:org/:unit/dashboards/:dashboardKey" element={<DashboardPage />} />
                </Route>
                <Route path="*" element={<Navigate to="/lexgroup/dashboards" replace />} />
            </Routes>
        </BrowserRouter>
    )
}

export default App