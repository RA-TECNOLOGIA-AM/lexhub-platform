import { Suspense } from 'react'
import { useParams } from 'react-router'
import { ErrorBoundary } from '../../components/states/ErrorBoundary.tsx'
import { LoadingState } from '../../components/states/LoadingState.tsx'
import { StateMessage } from '../../components/states/StateMessage.tsx'
import { DASHBOARD_PAGES } from './registry.tsx'

// Rota /:org/:unit/dashboards/:dashboardKey: procura a página do dashboard no registro.
export function DashboardPage() {
    const { dashboardKey = '' } = useParams()
    const Page = DASHBOARD_PAGES[dashboardKey]

    if (!Page) {
        return (
            <StateMessage icon="inbox" title="Em construção">
                O dashboard "{dashboardKey}" ainda não tem página na V2.
            </StateMessage>
        )
    }
    // O dashboard é baixado na 1ª vez que abre: enquanto isso, o mesmo esqueleto do carregamento dos dados.
    // Erro de render no dashboard fica só no miolo: topbar e menu continuam funcionando.
    return (
        <ErrorBoundary resetKey={dashboardKey} title="Este dashboard não abriu">
            <Suspense fallback={<LoadingState variant="dashboard" />}>
                <Page />
            </Suspense>
        </ErrorBoundary>
    )
}
