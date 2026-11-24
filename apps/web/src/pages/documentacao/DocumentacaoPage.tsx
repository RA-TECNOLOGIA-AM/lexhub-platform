import { useParams } from 'react-router'
import { PageHeader } from '../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../components/states/ErrorState.tsx'
import { LoadingState } from '../../components/states/LoadingState.tsx'
import { StateMessage } from '../../components/states/StateMessage.tsx'
import { Icon, type IconName } from '../../components/ui/Icon.tsx'
import { PageTransitionLink } from '../../components/page_transition/PageTransitionLink.tsx'
import { useAsync } from '../../hooks/useAsync.ts'
import { dataClient } from '../../services/client.ts'
import { DOC_ENTRIES, GUIDE_ENTRIES, visibleDocs } from './docRegistry.ts'

type IndexCardProps = { to: string; icon: IconName; title: string; description: string; tags?: string[] }

// Um card do índice (guia de uso ou de dashboard).
function IndexCard({ to, icon, title, description, tags = [] }: IndexCardProps) {
    return (
        <PageTransitionLink className="card dcard doc-index-card" to={to}>
            <span className="dcard-head">
                <span className="doc-metric-icon">
                    <Icon name={icon} size={18} />
                </span>
                <span className="title">{title}</span>
            </span>
            <span className="desc">{description}</span>
            {tags.length > 0 && (
                <span className="tags" style={{ marginTop: 'auto' }}>
                    {tags.map((t) => (
                        <span key={t} className="tag">
                            {t}
                        </span>
                    ))}
                </span>
            )}
        </PageTransitionLink>
    )
}

// Índice da documentação: os guias de uso (todo mundo vê) e um card por guia dos dashboards que a
// pessoa pode abrir (catálogo do hub, já em memória).
export function DocumentacaoPage() {
    const { org = '' } = useParams()
    const { data: catalog, error } = useAsync(() => dataClient.listDashboards(org), [org])

    if (error) return <ErrorState error={error} />
    if (!catalog) return <LoadingState />

    const docs = visibleDocs(DOC_ENTRIES, catalog.available)
    return (
        <>
            <PageHeader
                title="Documentação"
                description="Como usar o LexHub e o guia de cada dashboard disponível para você."
            />
            <section className="stack" aria-labelledby="doc-uso">
                <h2 id="doc-uso" className="doc-label">
                    Primeiros passos
                </h2>
                <div className="grid grid-cards">
                    {GUIDE_ENTRIES.map((g) => (
                        <IndexCard
                            key={g.slug}
                            to={`/${org}/documentacao/${g.slug}`}
                            icon="rocket"
                            title={g.title}
                            description={g.description}
                        />
                    ))}
                </div>
            </section>
            <section className="stack" aria-labelledby="doc-dashboards" style={{ marginTop: 28 }}>
                <h2 id="doc-dashboards" className="doc-label">
                    Guias dos dashboards
                </h2>
                {docs.length === 0 ? (
                    <StateMessage icon="book" title="Nenhuma documentação disponível">
                        Os guias aparecem aqui conforme os dashboards são liberados para você.
                    </StateMessage>
                ) : (
                    <div className="grid grid-cards">
                        {docs.map((doc) => (
                            <IndexCard
                                key={doc.slug}
                                to={`/${org}/documentacao/${doc.slug}`}
                                icon="book"
                                title={doc.title}
                                description={doc.description}
                                tags={doc.offices}
                            />
                        ))}
                    </div>
                )}
            </section>
        </>
    )
}
