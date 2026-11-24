import type { ReactNode } from 'react'
import { useParams } from 'react-router'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { PageTransitionLink } from '../../../components/page_transition/PageTransitionLink.tsx'
import { useAuth } from '../../../contexts/auth-context.ts'
import { rememberedUnit } from '../../../lib/activeUnit.ts'
import { DOC_ENTRIES } from '../docRegistry.ts'
import { useActiveSection } from './useActiveSection.ts'
import '../docs.css'

// Módulo: as peças de toda página de documentação. O conteúdo de cada guia (pasta conteudo/) só monta
// estas peças com o texto; o visual (docs.css) muda aqui sem mexer nos guias.

export type TocItem = { id: string; label: string }

type DocPageProps = {
    title: string
    intro: ReactNode // parágrafo abaixo do título
    tags?: string[] // ex.: ['NG', 'LA'] (unidades a que o guia se aplica)
    note?: string // etiqueta neutra ao lado das unidades (ex.: 'Banco lexpre — base nova')
    toc: TocItem[] // "Neste guia": âncoras das seções
    children: ReactNode // seções (DocSection) e avisos (InfoBox) logo abaixo do cabeçalho
    header?: ReactNode // avisos do cabeçalho (antes das seções)
    kicker?: string // degrau da trilha entre "Documentação" e o título (ex.: 'Primeiros passos')
}

// "01 — Indicadores" -> { num: '01', text: 'Indicadores' }; sem número na frente, num = null.
export function splitNumber(title: string): { num: string | null; text: string } {
    const match = /^(\d{1,2})\s*[—–-]\s*(.+)$/.exec(title)
    return match ? { num: match[1], text: match[2] } : { num: null, text: title }
}

// Os links do sumário; o da seção que está na tela fica marcado.
function TocLinks({ toc, active }: { toc: TocItem[]; active: string | null }) {
    return (
        <nav className="doc-toc" aria-label="Neste guia">
            {toc.map((item) => (
                <a key={item.id} href={`#${item.id}`} aria-current={item.id === active ? 'true' : undefined}>
                    {splitNumber(item.label).text}
                </a>
            ))}
        </nav>
    )
}

// A página: trilha, título, introdução e etiquetas; as seções em texto corrido e o sumário fixo à direita
// (no celular, "Neste guia" abre e fecha no topo). Guia de dashboard ganha o atalho para abrir o dashboard.
export function DocPage({ title, intro, tags = [], note, toc, header, kicker, children }: DocPageProps) {
    const { org = '', slug = '' } = useParams()
    const active = useActiveSection(toc.map((t) => t.id))
    const entry = DOC_ENTRIES.find((d) => d.slug === slug)
    return (
        <div className="doc">
            <div className="doc-layout">
                <article className="doc-article">
                    <header className="doc-head">
                        <nav className="doc-crumb" aria-label="Trilha">
                            <PageTransitionLink to={`/${org}/documentacao`}>Documentação</PageTransitionLink>
                            {kicker && (
                                <>
                                    <span aria-hidden="true">/</span>
                                    <span>{kicker}</span>
                                </>
                            )}
                        </nav>
                        <h1 className="h1">{title}</h1>
                        <p className="doc-intro">{intro}</p>
                        {(tags.length > 0 || note) && (
                            <div className="doc-meta">
                                {tags.map((t) => (
                                    <span key={t} className="doc-tag">
                                        {t}
                                    </span>
                                ))}
                                {note && <span className="doc-tag is-plain">{note}</span>}
                            </div>
                        )}
                        {header}
                    </header>

                    {toc.length > 0 && (
                        <details className="doc-toc-mobile">
                            <summary>Neste guia</summary>
                            <TocLinks toc={toc} active={active} />
                        </details>
                    )}

                    {children}
                </article>

                <aside className="doc-aside">
                    {toc.length > 0 && (
                        <>
                            <p className="doc-label">Neste guia</p>
                            <TocLinks toc={toc} active={active} />
                        </>
                    )}
                    {entry && (
                        <p className="doc-aside-foot">
                            <DashLink dashboard={entry.dashboards[0]} units={entry.units}>
                                Abrir o dashboard
                            </DashLink>
                        </p>
                    )}
                </aside>
            </div>
        </div>
    )
}

type DocSectionProps = {
    id: string
    title: string // "01 — Indicadores": o número fica à parte, em cinza
    subtitle?: string
    icon?: IconName // não aparece mais (texto corrido); mantido para não mexer nos guias
    children: ReactNode
}

// Uma seção: título e subtítulo, e o conteúdo em texto corrido (o id é a âncora do sumário).
export function DocSection({ id, title, subtitle, children }: DocSectionProps) {
    const { num, text } = splitNumber(title)
    return (
        <section id={id} className="doc-section">
            <div className="doc-section-head">
                <h2 className="doc-h2">
                    {num && <span className="doc-h2-num">{num}</span>}
                    {text}
                </h2>
                {subtitle && <p className="muted">{subtitle}</p>}
            </div>
            {children}
        </section>
    )
}

type MetricCardProps = {
    name: string
    icon?: IconName
    what: ReactNode // O que mede (fica à vista, abaixo do nome)
    counts?: ReactNode // O que é contado
    calc?: ReactNode // Como é calculado
    interpret?: ReactNode // Como interpretar
    caveat?: ReactNode // atenção (faixa destacada)
}

// Uma métrica que abre e fecha: nome e "o que mede" à vista; ao abrir, O que é contado · Como é calculado ·
// Como interpretar (+ atenção). Numa DocGrid, as métricas viram uma lista só (docs.css).
export function MetricCard({ name, icon, what, counts, calc, interpret, caveat }: MetricCardProps) {
    const rows: [string, ReactNode][] = [
        ['O que é contado', counts],
        ['Como é calculado', calc],
        ['Como interpretar', interpret],
    ]
    const filled = rows.filter(([, value]) => value != null && value !== '')
    return (
        <details className="doc-metric">
            <summary>
                <span className="doc-metric-icon" aria-hidden="true">
                    <Icon name={icon ?? 'barChart'} size={16} />
                </span>
                <span className="doc-metric-name">{name}</span>
                <span className="doc-metric-what">{what}</span>
                <span className="doc-metric-chev" aria-hidden="true">
                    <Icon name="chevron-down" size={16} />
                </span>
            </summary>
            <div className="doc-metric-body">
                {filled.length > 0 && (
                    <dl className="doc-dl">
                        {filled.map(([label, value]) => (
                            <div key={label} style={{ display: 'contents' }}>
                                <dt>{label}</dt>
                                <dd>{value}</dd>
                            </div>
                        ))}
                    </dl>
                )}
                {caveat && (
                    <div className="doc-caveat">
                        <Icon name="alert" size={14} />
                        <p>{caveat}</p>
                    </div>
                )}
            </div>
        </details>
    )
}

// Blocos lado a lado (DocCard) ou a lista de métricas (MetricCard).
export function DocGrid({ children }: { children: ReactNode }) {
    return <div className="doc-grid">{children}</div>
}

// Fórmula em destaque (ex.: "Comissão = R$ 1,00 × Qtd de protocolados").
export function Formula({ children }: { children: ReactNode }) {
    return <div className="doc-formula">{children}</div>
}

// Explicação em faixa, com o ícone de informação.
export function InfoBox({ children }: { children: ReactNode }) {
    return (
        <div className="doc-info">
            <Icon name="info" size={16} />
            <div>{children}</div>
        </div>
    )
}

// Bloco de texto com título: solto na seção é texto corrido; dentro de uma DocGrid, um quadro leve.
export function DocCard({ title, children }: { title?: string; children: ReactNode }) {
    return (
        <div className="doc-card">
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

export type DocStep = { title: string; body: ReactNode }

// Passos numerados ligados por uma linha (ex.: entrar numa TV: 1. na TV, 2. no celular, 3. autorizar).
export function DocSteps({ steps }: { steps: DocStep[] }) {
    return (
        <ol className="doc-steps">
            {steps.map((step, i) => (
                <li key={step.title} className="doc-step">
                    <span className="doc-step-num" aria-hidden="true">
                        {i + 1}
                    </span>
                    <div className="doc-step-body">
                        <strong>{step.title}</strong>
                        <div>{step.body}</div>
                    </div>
                </li>
            ))}
        </ol>
    )
}

// Tabela simples de texto (v1: DataTable). `code`: índices das colunas mostradas como nome técnico (ex.: [1]).
export function DocTable({ head, rows, code = [] }: { head: string[]; rows: ReactNode[][]; code?: number[] }) {
    return (
        <div className="card tblwrap">
            <table className="tbl">
                <thead>
                    <tr>
                        {head.map((h) => (
                            <th key={h}>{h}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row, i) => (
                        <tr key={i}>
                            {row.map((cell, j) => (
                                <td key={j}>{cell && code.includes(j) ? <Code>{cell}</Code> : cell}</td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
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
// units: só estas servem (ex.: guia do Recursal LA); a escolhida fora delas dá lugar à primeira que a pessoa vê.
export function DashLink({ dashboard, units, children }: { dashboard: string; units?: string[]; children: ReactNode }) {
    const { org = '' } = useParams()
    const { me } = useAuth()
    const fits = (code: string | null | undefined) => !!code && (!units || units.includes(code))
    const remembered = rememberedUnit(org)
    const unit = fits(remembered)
        ? remembered
        : (me?.units.find((u) => fits(u.code))?.code ?? remembered ?? me?.units[0]?.code ?? '')
    return (
        <PageTransitionLink className="doc-link" to={`/${org}/${unit}/dashboards/${dashboard}`}>
            {children}
        </PageTransitionLink>
    )
}
