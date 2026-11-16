import type { ReactNode } from 'react'
import { useAuth } from '../../contexts/auth-context.ts'
import type { DashboardSummary, Meta } from '../../types/index.ts'
import { Icon } from '../ui/Icon.tsx'
import { minutesSince } from '../../lib/format.ts'
import { unitName } from '../../lib/units.ts'
import { PageTransitionLink } from '../page_transition/PageTransitionLink.tsx'
import { DOC_ENTRIES, docFor } from '../../pages/documentacao/docRegistry.ts'
import { DOC_PAGES } from '../../pages/documentacao/docPages.ts'

type DashboardHeaderProps = {
    org: string
    dashboard: DashboardSummary // item do catálogo (título, área, descrição, limite de atraso)
    meta: Meta // de onde e de quando são os dados desta resposta
    actions?: ReactNode // botões à direita do título (Gerar comissão, Exportar, Atualizar)
}

// Cabeçalho comum dos dashboards: trilha (Dashboards · área · unidade · fonte), título, descrição e, à direita,
// as ações, a última atualização (no fuso da unidade; âmbar quando a fonte está atrasada) e o guia.
// A troca de unidade fica no seletor da barra lateral; Filtros e Período ficam na topbar.
export function DashboardHeader({ org, dashboard, meta, actions }: DashboardHeaderProps) {
    const { me } = useAuth()
    const entry = docFor(DOC_ENTRIES, dashboard.key, meta.unit)
    const doc = entry && DOC_PAGES[entry.slug] ? entry : null
    const late = meta.synced_at === null || minutesSince(meta.synced_at) > dashboard.max_delay_min
    return (
        <section className="dhead">
            <div className="dhead-main">
                <span className="dhead-trail">
                    <PageTransitionLink to={`/${org}/dashboards`}>Dashboards</PageTransitionLink>
                    {/* unidade e fonte com o mesmo nome (NG · NG) aparecem uma vez só */}
                    {[...new Set([dashboard.area, meta.unit, meta.source].filter(Boolean))].map((part) => (
                        <span key={part}> · {part}</span>
                    ))}
                </span>
                <div className="dhead-title">
                    <span className="dhead-icon" aria-hidden="true">
                        <Icon name="sheet" size={20} />
                    </span>
                    <h1 className="h1">
                        {dashboard.title} · {unitName(meta.unit, me?.units ?? [])}
                    </h1>
                </div>
                {dashboard.desc && <p className="dhead-desc">{dashboard.desc}</p>}
            </div>
            <div className="dhead-side">
                <div className="dhead-actions">
                    {actions}
                    <span className={late ? 'dhead-sync late' : 'dhead-sync'}>
                        {meta.synced_at === null
                            ? 'Aguardando sincronização'
                            : late
                              ? 'Fonte atrasada:'
                              : 'Última atualização:'}
                        {meta.synced_at && <span className="num">{dataHora(meta.synced_at, meta.timezone)}</span>}
                    </span>
                </div>
                {/* Atalho para o guia deste dashboard (só quando já existe na V2). */}
                {doc && (
                    <PageTransitionLink className="dhead-doc" to={`/${org}/documentacao/${doc.slug}`}>
                        <Icon name="book" size={16} />
                        Acessar Documentação
                    </PageTransitionLink>
                )}
            </div>
        </section>
    )
}

// '2026-11-13T21:29:18Z' -> '13/11/2026, 17:29:18' no fuso da unidade.
function dataHora(iso: string, timeZone: string): string {
    try {
        return new Date(iso).toLocaleString('pt-BR', { timeZone })
    } catch {
        return new Date(iso).toLocaleString('pt-BR')
    }
}
