import { useAuth } from '../../contexts/auth-context.ts'
import type { DashboardSummary, Meta } from '../../types/index.ts'
import { Freshness } from './Freshness.tsx'
import { Icon } from '../ui/Icon.tsx'
import { unitName } from '../../lib/units.ts'
import { PageTransitionLink } from '../page_transition/PageTransitionLink.tsx'
import { DOC_ENTRIES, docFor } from '../../pages/documentacao/docRegistry.ts'
import { DOC_PAGES } from '../../pages/documentacao/docPages.ts'

type DashboardHeaderProps = {
    org: string
    dashboard: DashboardSummary // item do catálogo (título, limite de atraso)
    meta: Meta // de onde e de quando são os dados desta resposta
}

// Cabeçalho comum dos dashboards: voltar, título com a unidade e selo de atualização.
// A troca de unidade fica no seletor da barra lateral; Período, Filtros e Exportar ficam na topbar e na faixa.
export function DashboardHeader({ org, dashboard, meta }: DashboardHeaderProps) {
    const { me } = useAuth()
    const entry = docFor(DOC_ENTRIES, dashboard.key, meta.unit)
    const doc = entry && DOC_PAGES[entry.slug] ? entry : null
    return (
        <section className="stack">
            <PageTransitionLink to={`/${org}/dashboards`} className="back-link">
                <Icon name="arrowLeft" size={16} />
                Dashboards
            </PageTransitionLink>
            <div className="stack" style={{ gap: 4 }}>
                <h1 className="h1">
                    {dashboard.title} · {unitName(meta.unit, me?.units ?? [])}
                </h1>
                <span className="row" style={{ gap: 16 }}>
                    <Freshness syncedAt={meta.synced_at} source={meta.source} maxDelayMin={dashboard.max_delay_min} />
                    {/* Atalho para o guia deste dashboard (só quando já existe na V2). */}
                    {doc && (
                        <PageTransitionLink className="doc-link small" to={`/${org}/documentacao/${doc.slug}`}>
                            Como ler este dashboard
                        </PageTransitionLink>
                    )}
                </span>
            </div>
        </section>
    )
}
