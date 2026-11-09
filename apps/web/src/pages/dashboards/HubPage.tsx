import { useParams, useSearchParams } from 'react-router'
import { useAuth } from '../../contexts/auth-context.ts'
import { CardSection } from '../../components/dashboard/CardSection.tsx'
import { DashboardCard } from '../../components/dashboard/DashboardCard.tsx'
import type { DashboardSummary } from '../../types/index.ts'
import { PillGroup, type PillItem } from '../../components/ui/PillGroup.tsx'
import { dataClient } from '../../services/client.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { ErrorState } from '../../components/states/ErrorState.tsx'
import { LoadingState } from '../../components/states/LoadingState.tsx'
import { useFavorites } from '../../hooks/useFavorites.ts'

export function HubPage() {
    const { org = '' } = useParams()
    const { me } = useAuth()
    const { data: catalog, error } = useAsync(() => dataClient.listDashboards(org), [org])
    const [searchParams] = useSearchParams()
    const unit = searchParams.get('unidade') // null = todas as unidades
    const favorites = useFavorites(org)

    if (error) return <ErrorState error={error} />
    if (!catalog || !favorites.ready) return <LoadingState />

    const all = catalog.available
    const dashboards = unit ? all.filter((d) => d.units.includes(unit)) : all

    // Pílulas: "Todas" + cada unidade que aparece no catálogo (nome do usuário logado quando houver).
    const unitName = (code: string) => me?.units.find((u) => u.code === code)?.name ?? code
    const unitCodes = [...new Set(all.flatMap((d) => d.units))]
    const pills: PillItem[] = [
        { id: 'todas', label: 'Todas as unidades', to: `/${org}/dashboards`, active: !unit },
        ...unitCodes.map((code) => ({
            id: code,
            label: unitName(code),
            to: `/${org}/dashboards?unidade=${code}`,
            active: code === unit,
        })),
    ]
    // Favoritos sobem para a seção do topo; o resto fica na sua área, na ordem do catálogo.
    const favs = dashboards.filter((d) => favorites.isFavorite(d.key))
    const others = dashboards.filter((d) => !favorites.isFavorite(d.key))
    const areas = [...new Set(others.map((d) => d.area))]
    const count = dashboards.length === 1 ? '1 dashboard liberado' : `${dashboards.length} dashboards liberados`

    // Um card do hub; usado nas duas seções.
    const card = (d: DashboardSummary) => (
        <DashboardCard
            key={d.key}
            org={org}
            unit={unit ?? d.units[0]}
            dashboard={d}
            favorite={favorites.isFavorite(d.key)}
            onToggleFavorite={() => favorites.toggle(d.key)}
        />
    )

    return (
        <>
            <section className="stack">
                <div className="stack" style={{ gap: 6 }}>
                    <h1 className="h1">Dashboards</h1>
                    <p className="muted">
                        {count} para você em {me?.org.name}.
                    </p>
                </div>
                <PillGroup label="Filtrar por unidade" items={pills} />
            </section>

            <div className="stack" style={{ gap: 22 }}>
                {favs.length > 0 && <CardSection title="Favoritos">{favs.map(card)}</CardSection>}
                {areas.map((area) => (
                    <CardSection key={area} title={area}>
                        {others.filter((d) => d.area === area).map(card)}
                    </CardSection>
                ))}
            </div>

            {catalog.upcoming.length > 0 && (
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
            )}
        </>
    )
}
