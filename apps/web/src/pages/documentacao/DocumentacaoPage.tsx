import { useState } from 'react'
import { useParams } from 'react-router'
import { PageHeader } from '../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../components/states/ErrorState.tsx'
import { LoadingState } from '../../components/states/LoadingState.tsx'
import { StateMessage } from '../../components/states/StateMessage.tsx'
import { Icon } from '../../components/ui/Icon.tsx'
import { Segmented } from '../../components/ui/Segmented.tsx'
import { PageTransitionLink } from '../../components/page_transition/PageTransitionLink.tsx'
import { useAsync } from '../../hooks/useAsync.ts'
import { dataClient } from '../../services/client.ts'
import { DOC_ENTRIES, GUIDE_ENTRIES, filterDocs, groupDocs, visibleDocs, type DocEntry } from './docRegistry.ts'
import './docs.css'

const ALL = 'todas'

// Uma linha da lista: título, descrição numa linha e as unidades.
function DocRow({ org, doc }: { org: string; doc: DocEntry }) {
    return (
        <PageTransitionLink className="doc-row" to={`/${org}/documentacao/${doc.slug}`}>
            <span className="doc-row-title">{doc.title}</span>
            <span className="doc-row-desc">{doc.description}</span>
            <span className="doc-row-units">
                {doc.offices.map((o) => (
                    <span key={o} className="doc-tag is-plain">
                        {o}
                    </span>
                ))}
            </span>
            <span className="doc-row-arrow" aria-hidden="true">
                <Icon name="chevron-right" size={16} />
            </span>
        </PageTransitionLink>
    )
}

// Índice da documentação: o guia de uso em destaque (todo mundo vê) e os guias dos dashboards que a pessoa
// pode abrir (catálogo do hub, já em memória), agrupados pela área, com busca e filtro de unidade.
export function DocumentacaoPage() {
    const { org = '' } = useParams()
    const { data: catalog, error } = useAsync(() => dataClient.listDashboards(org), [org])
    const [query, setQuery] = useState('')
    const [office, setOffice] = useState(ALL)

    if (error) return <ErrorState error={error} />
    if (!catalog) return <LoadingState />

    const docs = visibleDocs(DOC_ENTRIES, catalog.available)
    const groups = groupDocs(docs, catalog.available)
    const shown = filterDocs(groups, query, office === ALL ? null : office)
    const offices = [...new Set(docs.flatMap((d) => d.offices))]
    const guide = GUIDE_ENTRIES[0]

    return (
        <div className="doc-index">
            <PageHeader
                title="Documentação"
                description="Como usar o LexHub e o guia de cada dashboard liberado para você."
            />

            {guide && (
                <PageTransitionLink className="doc-hero" to={`/${org}/documentacao/${guide.slug}`}>
                    <span className="doc-hero-icon" aria-hidden="true">
                        <Icon name="rocket" size={22} />
                    </span>
                    <span className="doc-hero-text">
                        <strong>Novo por aqui? Comece pelo guia de uso</strong>
                        <span>{guide.description}</span>
                    </span>
                    <span className="doc-hero-go">Ler o guia →</span>
                </PageTransitionLink>
            )}

            {docs.length === 0 ? (
                <StateMessage icon="book" title="Nenhum guia de dashboard ainda">
                    Os guias aparecem aqui conforme os dashboards são liberados para você.
                </StateMessage>
            ) : (
                <>
                    <div className="doc-index-tools">
                        <input
                            className="field"
                            type="search"
                            placeholder="Buscar guia (ex.: comissão, recursal)"
                            aria-label="Buscar guia"
                            value={query}
                            onChange={(event) => setQuery(event.target.value)}
                            onKeyDown={(event) => {
                                if (event.key === 'Escape') setQuery('')
                            }}
                        />
                        {offices.length > 1 && (
                            <Segmented
                                label="Unidade"
                                options={[
                                    { value: ALL, label: 'Todas' },
                                    ...offices.map((o) => ({ value: o, label: o })),
                                ]}
                                value={office}
                                onChange={setOffice}
                            />
                        )}
                    </div>

                    {shown.length === 0 ? (
                        <StateMessage icon="search" title="Nenhum guia encontrado">
                            Tente outra palavra ou escolha "Todas" as unidades.
                        </StateMessage>
                    ) : (
                        shown.map((group) => (
                            <section key={group.area} className="doc-group" aria-label={group.area}>
                                <h2 className="doc-label">
                                    {group.area}
                                    <span>{group.docs.length}</span>
                                </h2>
                                <div className="doc-rows">
                                    {group.docs.map((doc) => (
                                        <DocRow key={doc.slug} org={org} doc={doc} />
                                    ))}
                                </div>
                            </section>
                        ))
                    )}
                </>
            )}
        </div>
    )
}
