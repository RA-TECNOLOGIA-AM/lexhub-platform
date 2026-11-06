import { useParams } from 'react-router'
import { ProtocoloPage } from './ProtocoloPage.tsx'

// A rota é uma só (/:org/:unit/dashboards/:dashboardKey); aqui se escolhe a página de cada dashboard.
export function DashboardPage() {
    const { dashboardKey } = useParams()

    switch (dashboardKey) {
        case 'protocolo-lexpre':
            return <ProtocoloPage />
        default:
            return (
                <section className="stack">
                    <h1 className="h1">Em construção</h1>
                    <p className="muted">O dashboard "{dashboardKey}" ainda não tem página na V2.</p>
                </section>
            )
    }
}