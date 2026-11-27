import { useRef, useState, type ReactNode, type RefObject } from 'react'
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
    note?: ReactNode // etiqueta neutra ao lado das unidades (ex.: 'Banco lexpre — base nova')
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

// Botão do sumário: abre (ou fecha) de uma vez todas as métricas do guia. Guia sem métricas: some (docs.css).
function ExpandAll({ article }: { article: RefObject<HTMLElement | null> }) {
    const [open, setOpen] = useState(false)
    function toggle() {
        const list = article.current?.querySelectorAll<HTMLDetailsElement>('details.doc-metric') ?? []
        const next = !Array.from(list).every((d) => d.open)
        list.forEach((d) => (d.open = next))
        setOpen(next)
    }
    return (
        <button type="button" className="doc-aside-btn doc-expand-all" onClick={toggle} aria-pressed={open}>
            {open ? 'Recolher todos os detalhes' : 'Expandir todos os detalhes'}
        </button>
    )
}

// A página: trilha, etiquetas, título e introdução; as seções em texto corrido e o sumário fixo à direita
// (no celular, "Neste guia" abre e fecha no topo). Guia de dashboard ganha o atalho para abrir o dashboard.
export function DocPage({ title, intro, tags = [], note, toc, header, kicker, children }: DocPageProps) {
    const { org = '', slug = '' } = useParams()
    const active = useActiveSection(toc.map((t) => t.id))
    const entry = DOC_ENTRIES.find((d) => d.slug === slug)
    const article = useRef<HTMLElement>(null)
    return (
        <div className="doc">
            <div className="doc-layout">
                <article className="doc-article" ref={article}>
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
                        <h1 className="h1">{title}</h1>
                        <p className="doc-intro">{intro}</p>
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
                    <div className="doc-aside-foot">
                        <ExpandAll article={article} />
                        {entry && (
                            <DashLink
                                className="doc-aside-btn is-primary"
                                dashboard={entry.dashboards[0]}
                                units={entry.units}
                            >
                                Abrir o dashboard <span aria-hidden="true">↗</span>
                            </DashLink>
                        )}
                    </div>
                </aside>
            </div>
        </div>
    )
}

type DocSectionProps = {
    id: string
    title: string // "01 — Indicadores": o número fica à parte, em cinza
    subtitle?: string
    icon?: IconName // seção sem número: o ícone vai na caixinha do número
    tone?: Tone // cor do número da seção
    badge?: ReactNode // selo à direita do título (ex.: 'Cards clicáveis')
    children: ReactNode
}

// Uma seção: número (ou ícone) em caixinha, título e subtítulo, selo opcional à direita, e o conteúdo (o id é a âncora
// do sumário).
export function DocSection({ id, title, subtitle, icon, tone = 'accent', badge, children }: DocSectionProps) {
    const { num, text } = splitNumber(title)
    return (
        <section id={id} className="doc-section">
            <div className="doc-section-head">
                {(num || icon) && (
                    <span className="doc-h2-num" data-tone={tone} aria-hidden={num ? undefined : 'true'}>
                        {num ?? <Icon name={icon!} size={16} />}
                    </span>
                )}
                <div className="doc-section-title">
                    <h2 className="doc-h2">{text}</h2>
                    {subtitle && <p className="muted">{subtitle}</p>}
                </div>
                {badge && (
                    <DocPill tone={tone} className="doc-section-badge">
                        {badge}
                    </DocPill>
                )}
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

// Blocos lado a lado (DocCard, DocFeature...) ou a lista de métricas (MetricCard). cols: colunas fixas
// (2 ou 3) em telas largas; sem ele, quantas couberem.
export function DocGrid({ cols, children }: { cols?: 2 | 3; children: ReactNode }) {
    return <div className={cols ? `doc-grid is-cols-${cols}` : 'doc-grid'}>{children}</div>
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
export function DashLink({
    dashboard,
    units,
    className = 'doc-link',
    children,
}: {
    dashboard: string
    units?: string[]
    className?: string
    children: ReactNode
}) {
    const { org = '' } = useParams()
    const { me } = useAuth()
    const fits = (code: string | null | undefined) => !!code && (!units || units.includes(code))
    const remembered = rememberedUnit(org)
    const unit = fits(remembered)
        ? remembered
        : (me?.units.find((u) => fits(u.code))?.code ?? remembered ?? me?.units[0]?.code ?? '')
    return (
        <PageTransitionLink className={className} to={`/${org}/${unit}/dashboards/${dashboard}`}>
            {children}
        </PageTransitionLink>
    )
}

// ---------- Peças do layout novo (guia do Comercial LexPre em diante) ----------

// Cor de destaque das peças: laranja da marca, azul, verde, vermelho, roxo, amarelo ou neutro (docs.css).
export type Tone = 'accent' | 'info' | 'ok' | 'danger' | 'violet' | 'warn' | 'neutral'

// Selo pequeno (ex.: '1 por cliente', 'Race Chart · Clicável'). mono: em fonte de código.
export function DocPill({
    tone = 'neutral',
    mono,
    className,
    children,
}: {
    tone?: Tone
    mono?: boolean
    className?: string
    children: ReactNode
}) {
    const cls = ['doc-pill', mono && 'is-mono', className].filter(Boolean).join(' ')
    return (
        <span className={cls} data-tone={tone}>
            {children}
        </span>
    )
}

// Trecho do texto em cor de destaque (ex.: 'total combinado' em verde). mono: valores (R$ 12 mi/trimestre).
export function Hl({ tone = 'accent', mono, children }: { tone?: Tone; mono?: boolean; children: ReactNode }) {
    return (
        <strong className={mono ? 'doc-hl is-mono' : 'doc-hl'} data-tone={tone}>
            {children}
        </strong>
    )
}

// Quadro de destaque com borda colorida à esquerda: título (caps = versalete, como no aviso do cabeçalho),
// selo opcional à direita e o texto; DocMini dentro dele vira os quadrinhos lado a lado.
export function DocCallout({
    title,
    badge,
    tone = 'accent',
    icon = 'info',
    caps,
    children,
}: {
    title: ReactNode
    badge?: ReactNode
    tone?: Tone
    icon?: IconName
    caps?: boolean
    children: ReactNode
}) {
    return (
        <div className="doc-callout" data-tone={tone}>
            <div className="doc-callout-head">
                <Icon name={icon} size={16} />
                <p className={caps ? 'doc-callout-title is-caps' : 'doc-callout-title'}>{title}</p>
                {badge && (
                    <DocPill tone={tone} mono>
                        {badge}
                    </DocPill>
                )}
            </div>
            <div className="doc-callout-body">{children}</div>
        </div>
    )
}

// Quadrinho com rótulo em versalete (dentro de um DocCallout ou de uma DocGrid).
export function DocMini({ label, children }: { label: string; children: ReactNode }) {
    return (
        <div className="doc-mini">
            <p className="doc-mini-label">{label}</p>
            <div>{children}</div>
        </div>
    )
}

// Moldura que agrupa peças de uma seção (ex.: o modelo de dados + o aviso logo abaixo).
export function DocPanel({ children }: { children: ReactNode }) {
    return <div className="doc-panel">{children}</div>
}

export type DocEntityProps = {
    name: string // nome da tabela (em fonte de código)
    badge?: ReactNode // ex.: '1 por cliente'
    tone?: Tone
    keyLabel?: string // rodapé: 'Chave temporal (Seção 01):'
    keyValue?: ReactNode // rodapé: 'Data de Assinatura'
    children: ReactNode
}

function DocEntity({ name, badge, tone = 'info', keyLabel, keyValue, children }: DocEntityProps) {
    return (
        <div className="doc-entity" data-tone={tone}>
            <div className="doc-entity-head">
                <code className="doc-entity-name">{name}</code>
                {badge && (
                    <DocPill tone={tone} mono>
                        {badge}
                    </DocPill>
                )}
            </div>
            <p>{children}</p>
            {(keyLabel || keyValue) && (
                <div className="doc-entity-key">
                    <span>{keyLabel}</span>
                    <strong>{keyValue}</strong>
                </div>
            )}
        </div>
    )
}

// Duas tabelas lado a lado ligadas pela cardinalidade no meio (ex.: atendimento 1 : N demandas).
export function DocRelation({
    left,
    right,
    cardinality,
    caption,
}: {
    left: DocEntityProps
    right: DocEntityProps
    cardinality: string
    caption?: string
}) {
    return (
        <div className="doc-relation">
            <DocEntity {...left} />
            <div className="doc-relation-link" aria-label={`Relação ${cardinality}${caption ? `, ${caption}` : ''}`}>
                <span className="doc-relation-card">{cardinality}</span>
                {caption && <span className="doc-relation-caption">{caption}</span>}
            </div>
            <DocEntity {...right} />
        </div>
    )
}

// Nota datada (histórico do card): a data num selo à esquerda, o texto ao lado.
export function DocNote({ date, children }: { date: string; children: ReactNode }) {
    return (
        <div className="doc-note">
            <DocPill tone="info" mono>
                {date}
            </DocPill>
            <p>{children}</p>
        </div>
    )
}

export type DocChip = { label: string; tone?: Tone }

// Linha de etiquetas com rótulo (ex.: '8 canais rastreados:' Campanha, Redes Sociais...).
export function DocChips({ label, items }: { label?: string; items: DocChip[] }) {
    return (
        <div className="doc-chips">
            {label && <span className="doc-chips-label">{label}</span>}
            {items.map((c) => (
                <span key={c.label} className="doc-chip" data-tone={c.tone ?? 'neutral'}>
                    {c.label}
                </span>
            ))}
        </div>
    )
}

// Quadro com título (colorido pelo tom), selo à direita e texto. framed: borda e fundo no tom (alertas,
// destaques); wide: ocupa duas colunas da DocGrid.
export function DocFeature({
    title,
    tone,
    icon,
    badge,
    badgeTone,
    badgeMono = true,
    framed,
    wide,
    children,
}: {
    title: ReactNode
    tone?: Tone
    icon?: IconName
    badge?: ReactNode
    badgeTone?: Tone
    badgeMono?: boolean
    framed?: boolean
    wide?: boolean
    children: ReactNode
}) {
    const cls = ['doc-feature', framed && 'is-framed', wide && 'is-wide'].filter(Boolean).join(' ')
    return (
        <div className={cls} data-tone={tone ?? 'neutral'}>
            <div className="doc-feature-head">
                <h3 className={tone ? 'doc-feature-title is-toned' : 'doc-feature-title'}>
                    {icon && <Icon name={icon} size={15} />}
                    {title}
                </h3>
                {badge && (
                    <DocPill tone={badgeTone ?? tone ?? 'neutral'} mono={badgeMono}>
                        {badge}
                    </DocPill>
                )}
            </div>
            <div className="doc-feature-body">{children}</div>
        </div>
    )
}

// Diferença para o legado: situação em selo (ex.: 'Em evolução'), área à direita, título e texto.
export function DocChange({
    status,
    tone = 'accent',
    area,
    title,
    framed,
    children,
}: {
    status: string
    tone?: Tone
    area?: string
    title: string
    framed?: boolean
    children: ReactNode
}) {
    return (
        <div className={framed ? 'doc-change is-framed' : 'doc-change'} data-tone={tone}>
            <div className="doc-change-head">
                <DocPill tone={tone} mono>
                    {status}
                </DocPill>
                {area && <span className="doc-change-area">{area}</span>}
            </div>
            <h3 className="doc-change-title">{title}</h3>
            <div className="doc-change-body">{children}</div>
        </div>
    )
}
