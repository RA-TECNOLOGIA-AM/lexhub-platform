import { useEffect, useState } from 'react'
import { useParams } from 'react-router'
import { useAuth } from '../auth/auth-context.ts'
import { DashboardCard } from '../components/DashboardCard.tsx'
import { dataClient } from '../data/client.ts'
import type { DashboardCatalog } from '../data/types.ts'

export function HubPage() {
    const { org = '' } = useParams()
    const { me } = useAuth()
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

    const dashboards = catalog.available
    // Áreas sem repetição, na ordem em que aparecem: ['Operação jurídica', ...]
    const areas = [...new Set(dashboards.map((d) => d.area))]
    const count = dashboards.length === 1 ? '1 dashboard liberado' : `${dashboards.length} dashboards liberados`

    return (
        <>
            <section className="stack">
                <div className="stack" style={{ gap: 6 }}>
                    <h1 className="h1">Dashboards</h1>
                    <p className="muted">
                        {count} para você em {me?.org.name}.
                    </p>
                </div>
            </section>

            <div className="stack" style={{ gap: 22 }}>
                {areas.map((area) => (
                    <section key={area} className="stack" aria-label={area}>
                        <h2 className="h2">{area}</h2>
                        <div className="grid grid-cards">
                            {dashboards
                                .filter((d) => d.area === area)
                                .map((d) => (
                                    <DashboardCard key={d.key} org={org} unit={d.units[0]} dashboard={d} />
                                ))}
                        </div>
                    </section>
                ))}
            </div>

            <section className="stack" aria-labelledby="soon-title">
                <div>
                    <h2 className="h2" id="soon-title">
                        Chegando na V2
                    </h2>
                    <p className="muted small">
                        Seguem na v1 até migrarem. Cada um entra aqui depois que os números baterem com a v1.
                    </p>
                </div>
                <div className="grid grid-cards">
                    {catalog.upcoming.map((d) => (
                        <div
                            key={d.title}
                            className="card dcard"
                            aria-disabled="true"
                            style={{ borderStyle: 'dashed', background: '#FAFBFC', cursor: 'default' }}
                        >
                            <span className="title">{d.title}</span>
                            <span className="desc">{d.area}</span>
                            <span className="tag" style={{ marginTop: 'auto', alignSelf: 'flex-start' }}>
                                Migrando da v1
                            </span>
                        </div>
                    ))}
                </div>
            </section>
        </>
    )
}