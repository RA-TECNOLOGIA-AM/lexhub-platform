import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from './auth-context.ts'
import { LoadingState } from '../components/states/LoadingState.tsx'

// Rota "porteiro": só deixa passar quem está logado; os outros vão para o /login,
// levando o endereço de onde vieram para voltar lá depois de entrar.
export function RequireAuth() {
    const { me, loading, rememberLocation } = useAuth()
    const location = useLocation()

    if (loading) {
        return (
            <main className="content">
                <LoadingState />
            </main>
        )
    }
    if (!me) {
        const state = rememberLocation ? { from: location.pathname + location.search } : undefined
        return <Navigate to="/login" replace state={state} />
    }    return <Outlet />
}