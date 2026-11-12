import { useParams } from 'react-router'
import { PageHeader } from '../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../components/states/ErrorState.tsx'
import { LoadingState } from '../../components/states/LoadingState.tsx'
import { StateMessage } from '../../components/states/StateMessage.tsx'
import { Icon } from '../../components/ui/Icon.tsx'
import { PageTransitionLink } from '../../components/page_transition/PageTransitionLink.tsx'
import { useAsync } from '../../hooks/useAsync.ts'
import { dataClient } from '../../services/client.ts'
import { DOC_ENTRIES, visibleDocs } from './docRegistry.ts'

// Índice da documentação: um card por guia dos dashboards que a pessoa pode abrir (catálogo do hub, já em memória).
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
                description="Guias de cada dashboard disponível para você. Escolha um para entender a lógica por trás de cada número."
            />
            {docs.length === 0 ? (
                <StateMessage icon="book" title="Nenhuma documentação disponível">
                    Os guias aparecem aqui conforme os dashboards são liberados para você.
                </StateMessage>
            ) : (
                <div className="grid grid-cards">
                    {docs.map((doc) => (
                        <PageTransitionLink
                            key={doc.slug}
                            className="card dcard doc-index-card"
                            to={`/${org}/documentacao/${doc.slug}`}
                        >
                            <span className="dcard-head">
                                <span className="doc-metric-icon">
                                    <Icon name="book" size={18} />
                                </span>
                                <span className="title">{doc.title}</span>
                            </span>
                            <span className="desc">{doc.description}</span>
                            <span className="tags" style={{ marginTop: 'auto' }}>
                                {doc.offices.map((o) => (
                                    <span key={o} className="tag">
                                        {o}
                                    </span>
                                ))}
                            </span>
                        </PageTransitionLink>
                    ))}
                </div>
            )}
        </>
    )
}
