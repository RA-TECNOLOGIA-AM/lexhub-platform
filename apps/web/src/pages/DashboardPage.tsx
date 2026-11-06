import { useParams } from 'react-router'

export function DashboardPage() {
    const { org, unit, dashboardKey } = useParams()
    return (
        <h1 className="h1">
            Dashboard {dashboardKey} · {org} / {unit}
        </h1>
    )
}