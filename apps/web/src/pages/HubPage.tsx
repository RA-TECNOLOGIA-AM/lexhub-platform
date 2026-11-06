import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { dataClient } from '../data/client.ts'
import type { DashboardCatalog } from '../data/types.ts'

export function HubPage() {
    const { org = '' } = useParams()
    const [catalog, setCatalog] = useState<DashboardCatalog | null>(null)

    useEffect(() => {
        let ignore = false
        dataClient.listDashboards(org).then((data) => {
            if (!ignore) setCatalog(data)
        })
        return () => {
            ignore = true
        }
    }, [org])

    if (!catalog) return <p className="muted">Carregando…</p>

    return (
        <section className="stack">
            <h1 className="h1">Dashboards</h1>
            <ul>
                {catalog.available.map((d) => (
                    <li key={d.key}>
                        <Link to={`/${org}/${d.units[0]}/dashboards/${d.key}`}>{d.title}</Link>
                    </li>
                ))}
            </ul>
        </section>
    )
}