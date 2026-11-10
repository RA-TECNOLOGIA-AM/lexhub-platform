import { Link, useParams, useSearchParams } from 'react-router'
import { useAuth } from '../../contexts/auth-context.ts'
import { DashboardCard } from '../../components/dashboard/DashboardCard.tsx'
import { HubDnd, type HubDrop } from '../../components/dashboard/HubDnd.tsx'
import { SortableCard } from '../../components/dashboard/SortableCard.tsx'
import { SortableSection } from '../../components/dashboard/SortableSection.tsx'
import type { DashboardSummary } from '../../types/index.ts'
import { PillGroup, type PillItem } from '../../components/ui/PillGroup.tsx'
import { dataClient } from '../../services/client.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { ErrorState } from '../../components/states/ErrorState.tsx'
import { LoadingState } from '../../components/states/LoadingState.tsx'
import { StateMessage } from '../../components/states/StateMessage.tsx'
import { useFavorites } from '../../hooks/useFavorites.ts'
import { useHubOrder } from '../../hooks/useHubOrder.ts'
import { sortAreas, sortByOrder } from '../../lib/hubOrder.ts'
import { searchDashboards, SEARCH_PARAM } from '../../lib/dashboardSearch.ts'
import { unitName } from '../../lib/units.ts'

const FAVORITES = 'Favoritos'

export function HubPage() {
    const { org = '' } = useParams()
    const { me } = useAuth()
    const { data: catalog, error } = useAsync(() => dataClient.listDashboards(org), [org])
    const [searchParams] = useSearchParams()
    const unit = searchParams.get('unidade') // null = todas as unidades
    const query = searchParams.get(SEARCH_PARAM) ?? '' // texto da busca do topo ('' = sem busca)
    const favorites = useFavorites(org)
    const hubOrder = useHubOrder(org)

    if (error) return <ErrorState error={error} />
    if (!catalog || !favorites.ready || !hubOrder.ready) return <LoadingState />

    // O catálogo na ordem que a pessoa arrastou (dashboard novo vai para o fim).
    const all = sortByOrder(catalog.available, hubOrder.order)
    // Primeiro a unidade, depois a busca. notFound = buscou e nada combinou.
    const byUnit = unit ? all.filter((d) => d.units.includes(unit)) : all
    const dashboards = searchDashboards(byUnit, query)
    const searching = query.trim() !== ''
    const notFound = searching && dashboards.length === 0
    // Pílulas: "Todas" + cada unidade que aparece no catálogo (nome do usuário logado quando houver).
    // Lê do catálogo original: arrastar cards não muda a ordem das pílulas.
    const unitCodes = [...new Set(catalog.available.flatMap((d) => d.units))]
    const pills: PillItem[] = [
        { id: 'todas', label: 'Todas as unidades', to: `/${org}/dashboards`, active: !unit },
        ...unitCodes.map((code) => ({
            id: code,
            label: unitName(code, me?.units ?? []),
            to: `/${org}/dashboards?unidade=${code}`,
            active: code === unit,
        })),
    ]
    // Favoritos sobem para a seção do topo; o resto fica na sua área.
    const favs = dashboards.filter((d) => favorites.isFavorite(d.key))
    const others = dashboards.filter((d) => !favorites.isFavorite(d.key))
    // Áreas na ordem do catálogo, com as prioritárias (Gestão) logo abaixo de Favoritos.
    const areas = sortAreas([...new Set(catalog.available.map((d) => d.area))]).filter((area) =>
        others.some((d) => d.area === area),
    )
    const count =
        dashboards.length === 0
            ? 'Nenhum dashboard liberado'
            : dashboards.length === 1
              ? '1 dashboard liberado'
              : `${dashboards.length} dashboards liberados`

    // O que fazer ao soltar um card: na mesma seção, reordena; de uma área para Favoritos, favorita
    // (e põe onde caiu). Qualquer outro caso (ex.: Favoritos -> área) é ignorado: desfavoritar é pela estrela.
    function handleDrop({ active, from, over, to }: HubDrop) {
        if (to === FAVORITES && from !== FAVORITES) favorites.toggle(active)
        else if (to !== from) return
        // Ordem completa (todas as unidades): o filtro da tela não pode apagar a posição dos outros cards.
        if (over)
            hubOrder.move(
                all.map((d) => d.key),
                active,
                over,
            )
    }

    // Um card do hub, arrastável dentro da sua seção.
    const card = (section: string) => (d: DashboardSummary) => (
        <SortableCard key={d.key} id={d.key} section={section}>
            <DashboardCard
                org={org}
                unit={unit ?? d.units[0]}
                dashboard={d}
                favorite={favorites.isFavorite(d.key)}
                onToggleFavorite={() => favorites.toggle(d.key)}
            />
        </SortableCard>
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

            <HubDnd onDrop={handleDrop}>
                <div className="stack" style={{ gap: 22 }}>
                    {/* Organização sem nenhum dashboard (ex.: em implantação): explica em vez de mostrar a página vazia. */}
                    {all.length === 0 && (
                        <StateMessage icon="inbox" title="Nenhum dashboard liberado ainda">
                            Eles aparecem aqui quando as fontes de dados estiverem ligadas e um admin liberar dashboards
                            para a sua equipe.
                        </StateMessage>
                    )}
                    {/* Buscou e nada combinou: explica e oferece limpar a busca (mantendo a unidade). */}
                    {all.length > 0 && notFound && (
                        <StateMessage
                            icon="search"
                            title={`Nenhum dashboard encontrado para “${query.trim()}”`}
                            action={
                                <Link
                                    className="btn"
                                    to={unit ? `/${org}/dashboards?unidade=${unit}` : `/${org}/dashboards`}
                                >
                                    Limpar busca
                                </Link>
                            }
                        >
                            Confira a grafia ou busque pelo nome da área (ex.: Gestão).
                        </StateMessage>
                    )}
                    {/* Favoritos aparece mesmo vazio: é onde se solta um card para favoritar. */}
                    {all.length > 0 && !notFound && (favs.length > 0 || !searching) && (
                        <SortableSection title={FAVORITES} ids={favs.map((d) => d.key)} acceptsOthers>
                            {favs.length > 0 ? (
                                favs.map(card(FAVORITES))
                            ) : (
                                <p className="card drop-hint muted small">
                                    Arraste um card para cá ou toque na estrela para favoritar.
                                </p>
                            )}
                        </SortableSection>
                    )}
                    {areas.map((area) => {
                        const items = others.filter((d) => d.area === area)
                        return (
                            <SortableSection key={area} title={area} ids={items.map((d) => d.key)}>
                                {items.map(card(area))}
                            </SortableSection>
                        )
                    })}
                </div>
            </HubDnd>

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
