import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from './auth-context.ts'

// Rota "porteiro": só deixa passar quem está logado; os outros vão para o /login,
// levando o endereço de onde vieram para voltar lá depois de entrar.
export function RequireAuth() {
    const { me, loading } = useAuth()
    const location = useLocation()

    if (loading) return <p className="muted" style={{ padding: 24 }}>Carregando…</p>
    if (!me) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
    return <Outlet />
}