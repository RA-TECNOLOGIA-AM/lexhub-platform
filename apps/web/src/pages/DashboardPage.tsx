import { useParams } from 'react-router'
import { StateMessage } from '../components/states/StateMessage.tsx'
import { DASHBOARD_PAGES } from '../dashboards/registry.tsx'

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
    return <Page />
}