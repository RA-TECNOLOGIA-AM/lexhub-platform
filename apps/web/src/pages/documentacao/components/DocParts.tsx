import type { ReactNode } from 'react'
import { useParams } from 'react-router'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { PageTransitionLink } from '../../../components/page_transition/PageTransitionLink.tsx'
import { useAuth } from '../../../contexts/auth-context.ts'
import { rememberedUnit } from '../../../lib/activeUnit.ts'

// Módulo: as peças de toda página de documentação (as mesmas da v1, com o visual da V2).
// O conteúdo de cada dashboard (pasta conteudo/) só monta estas peças com o texto.

export type TocItem = { id: string; label: string }

type DocPageProps = {
    title: string
    intro: ReactNode // parágrafo abaixo do título
    tags?: string[] // ex.: ['NG', 'LA'] (unidades a que o guia se aplica)
    note?: string // etiqueta neutra ao lado das unidades (ex.: 'Banco lexpre — base nova')
    toc: TocItem[] // "Neste guia": âncoras das seções
    children: ReactNode // seções (DocSection) e avisos (InfoBox) logo abaixo do cabeçalho
    header?: ReactNode // avisos do cabeçalho (antes do sumário)
}

// A página: voltar, título, introdução, unidades, sumário e as seções.
export function DocPage({ title, intro, tags = [], note, toc, header, children }: DocPageProps) {
    const { org = '' } = useParams()
    return (
        <article className="doc stack" style={{ gap: 28 }}>
            <header className="stack" style={{ gap: 14 }}>
                <PageTransitionLink to={`/${org}/documentacao`} className="back-link">
                    <Icon name="arrowLeft" size={16} />
                    Documentação
                </PageTransitionLink>
                <div className="stack" style={{ gap: 8 }}>
                    <p className="doc-kicker">Documentação · Dashboard</p>
                    <h1 className="h1">{title}</h1>
                    <p className="doc-intro">{intro}</p>
                </div>
                {(tags.length > 0 || note) && (
                    <div className="tags">
                        {tags.map((t) => (
                            <span key={t} className="doc-tag">
                                {t}
                            </span>
                        ))}
                        {note && <span className="tag">{note}</span>}
                    </div>
                )}
                {header}
            </header>

            {toc.length > 0 && (
                <nav className="card doc-toc" aria-label="Neste guia">
                    <p className="doc-label">Neste guia</p>
                    <div className="doc-toc-grid">
                        {toc.map((item) => (
                            <a key={item.id} href={`#${item.id}`}>
                                {item.label}
                            </a>
                        ))}
                    </div>
                </nav>
            )}

            {children}
        </article>
    )
}

type DocSectionProps = {
    id: string
    title: string
    subtitle?: string
    icon: IconName
    children: ReactNode
}

// Uma seção com ícone, título e subtítulo (o id é a âncora do sumário).
export function DocSection({ id, title, subtitle, icon, children }: DocSectionProps) {
    return (
        <section id={id} className="doc-section stack">
            <div className="doc-section-head">
                <span className="doc-section-icon">
                    <Icon name={icon} size={18} />
                </span>
                <div>
                    <h2 className="doc-h2">{title}</h2>
                    {subtitle && <p className="muted small">{subtitle}</p>}
                </div>
            </div>
            {children}
        </section>
    )
}

type MetricCardProps = {
    name: string
    icon?: IconName
    what: ReactNode // O que mede
    counts?: ReactNode // O que é contado
    calc?: ReactNode // Como é calculado
    interpret?: ReactNode // Como interpretar
    caveat?: ReactNode // atenção (caixa destacada)
}

// O cartão de uma métrica: O que mede · O que é contado · Como é calculado · Como interpretar (+ atenção).
export function MetricCard({ name, icon, what, counts, calc, interpret, caveat }: MetricCardProps) {
    const rows: [string, ReactNode][] = [
        ['O que mede', what],
        ['O que é contado', counts],
        ['Como é calculado', calc],
        ['Como interpretar', interpret],
    ]
    return (
        <div className="card doc-metric">
            <div className="doc-metric-head">
                {icon && (
                    <span className="doc-metric-icon">
                        <Icon name={icon} size={16} />
                    </span>
                )}
                <h3 className="doc-h3">{name}</h3>
            </div>
            <dl className="doc-dl">
                {rows
                    .filter(([, value]) => value != null && value !== '')
                    .map(([label, value]) => (
                        <div key={label}>
                            <dt className="doc-label">{label}</dt>
                            <dd>{value}</dd>
                        </div>
                    ))}
            </dl>
            {caveat && (
                <div className="doc-caveat">
                    <Icon name="alert" size={14} />
                    <p>{caveat}</p>
                </div>
            )}
        </div>
    )
}

// Grade de cartões (MetricCard ou DocCard), 2 a 3 por linha conforme a largura.
export function DocGrid({ children }: { children: ReactNode }) {
    return <div className="doc-grid">{children}</div>
}

// Fórmula em destaque (ex.: "Comissão = R$ 1,00 × Qtd de protocolados").
export function Formula({ children }: { children: ReactNode }) {
    return <div className="doc-formula">{children}</div>
}

// Caixa de explicação com o ícone de informação.
export function InfoBox({ children }: { children: ReactNode }) {
    return (
        <div className="doc-info">
            <Icon name="info" size={16} />
            <div>{children}</div>
        </div>
    )
}

// Bloco de texto livre com título (os "cards" de explicação da v1).
export function DocCard({ title, children }: { title?: string; children: ReactNode }) {
    return (
        <div className="card doc-card stack">
            {title && <h3 className="doc-h3">{title}</h3>}
            {children}
        </div>
    )
}

// Destaque "o que muda em relação à v1/legado" (v1: DiffBox).
export function DiffBox({ title, children }: { title?: string; children: ReactNode }) {
    return (
        <div className="doc-diff">
            {title && <p className="doc-h3">{title}</p>}
            <div>{children}</div>
        </div>
    )
}

// Destaque "fique de olho" (v1: WatchBox).
export function WatchBox({ title, children }: { title?: string; children: ReactNode }) {
    return (
        <div className="doc-watch">
            <Icon name="alert" size={16} />
            <div>
                {title && <p className="doc-h3">{title}</p>}
                {children}
            </div>
        </div>
    )
}

// Nome técnico no meio do texto (tabela, campo, setor_id...).
export function Code({ children }: { children: ReactNode }) {
    return <code className="doc-code">{children}</code>
}

// Link para outra documentação, pela chave do registro (ex.: 'org-documentos-lexpre').
export function DocLink({ to, children }: { to: string; children: ReactNode }) {
    const { org = '' } = useParams()
    return (
        <PageTransitionLink className="doc-link" to={`/${org}/documentacao/${to}`}>
            {children}
        </PageTransitionLink>
    )
}

// Link para o dashboard, na unidade escolhida no seletor (ou na primeira que a pessoa vê).
export function DashLink({ dashboard, children }: { dashboard: string; children: ReactNode }) {
    const { org = '' } = useParams()
    const { me } = useAuth()
    const unit = rememberedUnit(org) ?? me?.units[0]?.code ?? ''
    return (
        <PageTransitionLink className="doc-link" to={`/${org}/${unit}/dashboards/${dashboard}`}>
            {children}
        </PageTransitionLink>
    )
}
