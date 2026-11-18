import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router'
import { useAuth } from '../../contexts/auth-context.ts'
import { DashboardCard } from '../../components/dashboard/DashboardCard.tsx'
import { HubDnd, type HubDrop } from '../../components/dashboard/HubDnd.tsx'
import { SortableCard } from '../../components/dashboard/SortableCard.tsx'
import { SortableSection } from '../../components/dashboard/SortableSection.tsx'
import { BoardColumn } from '../../components/dashboard/BoardColumn.tsx'
import { Segmented } from '../../components/ui/Segmented.tsx'
import { storedHubView, storeHubView, type HubView } from '../../lib/hubView.ts'
import type { DashboardCatalog, DashboardSummary } from '../../types/index.ts'
import { withEnabled } from '../../lib/dashboardSwitch.ts'
import { hubUnit, rememberedUnit } from '../../lib/activeUnit.ts'
import { dataClient } from '../../services/client.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { ErrorState } from '../../components/states/ErrorState.tsx'
import { LoadingState } from '../../components/states/LoadingState.tsx'
import { StateMessage } from '../../components/states/StateMessage.tsx'
import { useFavorites } from '../../hooks/useFavorites.ts'
import { useHubOrder } from '../../hooks/useHubOrder.ts'
import { HUB_AREAS, sortAreas, sortByOrder } from '../../lib/hubOrder.ts'
import { searchDashboards, SEARCH_PARAM } from '../../lib/dashboardSearch.ts'
import { unitName } from '../../lib/units.ts'
import { PageTransitionLink } from '../../components/page_transition/PageTransitionLink.tsx'

const FAVORITES = 'Favoritos'
const VIEW_OPTIONS: { value: HubView; label: string; icon: 'grid' | 'list' }[] = [
    { value: 'quadro', label: 'Quadro', icon: 'grid' },
    { value: 'lista', label: 'Lista', icon: 'list' },
]
const MIGRATING = 'Os dashboards desta área estão sendo migrados da v1.'
const FAV_HINT = 'Arraste um card para cá ou toque na estrela para favoritar.'

export function HubPage() {
    const { org = '' } = useParams()
    const { me } = useAuth()
    const { data: loaded, error } = useAsync(() => dataClient.listDashboards(org), [org])
    // Depois de o Dev ligar/desligar um dashboard: o catálogo com a mudança (vale só para esta org).
    const [changed, setChanged] = useState<{ org: string; catalog: DashboardCatalog } | null>(null)
    const catalog = changed?.org === org ? changed.catalog : loaded
    const [searchParams] = useSearchParams()
    // A unidade do seletor da barra lateral: a da URL, ou a lembrada na sessão (null = todas as unidades).
    const unit = hubUnit(searchParams.get('unidade'), rememberedUnit(org), me?.units ?? [])
    const query = searchParams.get(SEARCH_PARAM) ?? '' // texto da busca do topo ('' = sem busca)
    const favorites = useFavorites(org)
    const hubOrder = useHubOrder(org)
    // Lista (seções) ou Quadro (colunas): escolha da pessoa, lembrada neste navegador.
    const [view, setView] = useState<HubView>(() => storedHubView())
    function changeView(next: HubView) {
        setView(next)
        storeHubView(next)
    }

    if (error) return <ErrorState error={error} />
    if (!catalog || !favorites.ready || !hubOrder.ready) return <LoadingState />

    // O catálogo na ordem que a pessoa arrastou (dashboard novo vai para o fim).
    const all = sortByOrder(catalog.available, hubOrder.order)
    // Primeiro a unidade, depois a busca. notFound = buscou e nada combinou.
    const byUnit = unit ? all.filter((d) => d.units.includes(unit)) : all
    const dashboards = searchDashboards(byUnit, query)
    const searching = query.trim() !== ''
    const notFound = searching && dashboards.length === 0
    // Favoritos sobem para a seção do topo; o resto fica na sua área.
    const favs = dashboards.filter((d) => favorites.isFavorite(d.key))
    const others = dashboards.filter((d) => !favorites.isFavorite(d.key))
    // As abas fixas (HUB_AREAS) aparecem sempre, mesmo vazias, em qualquer unidade (só a busca esconde as vazias);
    // as outras áreas só quando têm card.
    const showEmpty = !searching
    const areas = sortAreas([...new Set([...HUB_AREAS, ...catalog.available.map((d) => d.area)])]).filter(
        (area) => others.some((d) => d.area === area) || (showEmpty && HUB_AREAS.includes(area)),
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

    // Só o Desenvolvedor (o menu do card só aparece com can_toggle; a API confere de novo).
    async function setEnabled(key: string, unitCode: string, enabled: boolean) {
        await dataClient.setDashboardEnabled(org, unitCode, key, enabled)
        setChanged((prev) => {
            const base = prev?.org === org ? prev.catalog : catalog
            return base ? { org, catalog: withEnabled(base, key, unitCode, enabled) } : prev
        })
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
                showUnits={!unit}
                onSetEnabled={(unitCode, enabled) => setEnabled(d.key, unitCode, enabled)}
            />
        </SortableCard>
    )

    return (
        <>
            <section className="stack">
                <div className="hub-head">
                    <h1 className="h1">Dashboards</h1>
                    <Segmented
                        label="Visualização"
                        className="view-toggle"
                        options={VIEW_OPTIONS}
                        value={view}
                        onChange={changeView}
                    />
                </div>
                <div className="stack" style={{ gap: 6 }}>
                    <p className="muted">
                        {count} para você em {me?.org.name}
                        {unit ? ` · ${unitName(unit, me?.units ?? [])}` : ''}. Troque a unidade no seletor da barra
                        lateral.
                    </p>
                </div>
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
                                <PageTransitionLink
                                    className="btn"
                                    to={unit ? `/${org}/dashboards?unidade=${unit}` : `/${org}/dashboards`}
                                >
                                    Limpar busca
                                </PageTransitionLink>
                            }
                        >
                            Confira a grafia ou busque pelo nome da área (ex.: Pré-protocolo).
                        </StateMessage>
                    )}
                    {all.length > 0 && !notFound && view === 'lista' && (
                        <>
                            {/* Favoritos aparece mesmo vazio: é onde se solta um card para favoritar. */}
                            {(favs.length > 0 || !searching) && (
                                <SortableSection title={FAVORITES} ids={favs.map((d) => d.key)} acceptsOthers>
                                    {favs.length > 0 ? (
                                        favs.map(card(FAVORITES))
                                    ) : (
                                        <p className="card drop-hint muted small">{FAV_HINT}</p>
                                    )}
                                </SortableSection>
                            )}
                            {areas.map((area) => {
                                const items = others.filter((d) => d.area === area)
                                return (
                                    <SortableSection key={area} title={area} ids={items.map((d) => d.key)}>
                                        {items.length > 0 ? (
                                            items.map(card(area))
                                        ) : (
                                            <p className="card drop-hint muted small">{MIGRATING}</p>
                                        )}
                                    </SortableSection>
                                )
                            })}
                        </>
                    )}
                    {/* Quadro: uma coluna por área, lado a lado (rola na horizontal). Coluna vazia vira faixa estreita. */}
                    {all.length > 0 && !notFound && view === 'quadro' && (
                        <div className="board">
                            {(favs.length > 0 || !searching) && (
                                <BoardColumn
                                    title={FAVORITES}
                                    ids={favs.map((d) => d.key)}
                                    acceptsOthers
                                    empty={<p className="board-hint muted small">{FAV_HINT}</p>}
                                >
                                    {favs.map(card(FAVORITES))}
                                </BoardColumn>
                            )}
                            {areas.map((area) => {
                                const items = others.filter((d) => d.area === area)
                                return (
                                    <BoardColumn key={area} title={area} ids={items.map((d) => d.key)}>
                                        {items.map(card(area))}
                                    </BoardColumn>
                                )
                            })}
                        </div>
                    )}
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
                                style={{ borderStyle: 'dashed', background: 'var(--card-muted)', cursor: 'default' }}
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
