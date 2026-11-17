import { useState } from 'react'
import { niceScale, spreadLabels } from '../../lib/charts.ts'
import { fmt } from '../../lib/format.ts'
import { ChartEmpty } from './ChartCard.tsx'
import { useWidth } from './useWidth.ts'

export type ColumnSeries = { label: string; color: string; values: number[] } // color = var(--chart-1)...

type ColumnChartProps = {
    categories: string[]
    series: ColumnSeries[] // empilhadas, de baixo para cima
    height?: number
    format?: (v: number) => string
    selected?: string[]
    onSelect?: (category: string) => void
    selectLabel?: string
    caption?: string // título do eixo x, embaixo (ex.: "Mês de entrada")
    className?: string
    // Valor de cada parte da pilha (não só da primeira): dentro da parte quando cabe; parte fina, ao lado da
    // coluna, na cor da parte.
    partValues?: boolean
    tooltip?: boolean // caixa com o valor de cada parte ao passar o cursor (ou focar) numa coluna
}

const PAD = { top: 26, right: 12, bottom: 44, left: 40 }
const MIN_IN = 17 // altura mínima (px) da parte para o valor caber dentro dela
const TIP_W = 220 // largura da caixa do tooltip (para decidir o lado da coluna em que ela abre)

// Módulo: colunas verticais, empilhadas quando há mais de uma série (Demandas por funcionário,
// Não protocolados por mês). O total vai em cima; o valor de cada parte, dentro dela quando cabe.
export function ColumnChart({
    categories,
    series,
    height = 300,
    format = fmt.int,
    selected = [],
    onSelect,
    selectLabel = 'Filtrar por',
    caption,
    className,
    partValues = false,
    tooltip = false,
}: ColumnChartProps) {
    const [ref, width] = useWidth<HTMLDivElement>()
    const [hover, setHover] = useState<number | null>(null)
    const totals = categories.map((_, i) => series.reduce((sum, s) => sum + (s.values[i] ?? 0), 0))
    if (categories.length === 0 || totals.every((t) => t === 0)) {
        return (
            <div ref={ref}>
                <ChartEmpty />
            </div>
        )
    }

    const { max, ticks } = niceScale(Math.max(...totals))
    const plotW = Math.max(width - PAD.left - PAD.right, 40)
    const plotH = height - PAD.top - PAD.bottom
    const band = plotW / categories.length
    const barW = Math.min(band * 0.55, 110)
    const y = (v: number) => PAD.top + plotH - (v / max) * plotH
    const maxChars = Math.max(4, Math.floor(band / 7))
    // Nome que não cabe: o primeiro nome; ainda assim grande, cortado com reticências.
    const short = (s: string) => {
        if (s.length <= maxChars) return s
        const first = s.split(' ')[0]
        return first.length <= maxChars ? first : s.slice(0, maxChars - 1) + '…'
    }

    return (
        <div ref={ref} className={`chart-svg col-wrap${className ? ` ${className}` : ''}`}>
            <svg width={width} height={height} role="img" aria-label={describe(categories, series, format)}>
                {ticks.map((t) => (
                    <g key={t}>
                        <line className="chart-grid" x1={PAD.left} x2={PAD.left + plotW} y1={y(t)} y2={y(t)} />
                        <text className="chart-axis" x={PAD.left - 8} y={y(t)} dy="0.32em" textAnchor="end">
                            {fmt.int(t)}
                        </text>
                    </g>
                ))}
                {categories.map((cat, i) => {
                    const x = PAD.left + band * i + (band - barW) / 2
                    const dim = selected.length > 0 && !selected.includes(cat)
                    let base = 0
                    const parts = series.map((s) => {
                        const v = s.values[i] ?? 0
                        const top = base + v
                        const part = { s, v, y0: y(base), y1: y(top) }
                        base = top
                        return part
                    })
                    const thin = partValues ? parts.filter((p) => p.v > 0 && p.y0 - p.y1 < MIN_IN) : []
                    const thinY = spreadLabels(thin.map((p) => (p.y0 + p.y1) / 2))
                    return (
                        <g key={cat} className={dim ? 'chart-col dim' : 'chart-col'}>
                            {parts.map(({ s, v, y0, y1 }, k) =>
                                v > 0 ? (
                                    <g key={s.label}>
                                        <rect
                                            x={x}
                                            y={y1}
                                            width={barW}
                                            height={y0 - y1}
                                            rx={6}
                                            style={{ fill: s.color }}
                                        />
                                        {/* Como na v1: o valor da primeira série dentro da barra (o total vai em cima). */}
                                        {(partValues || (series.length > 1 && k === 0)) && y0 - y1 >= MIN_IN && (
                                            <text className="chart-in" x={x + barW / 2} y={(y0 + y1) / 2} dy="0.32em">
                                                {format(v)}
                                            </text>
                                        )}
                                    </g>
                                ) : null,
                            )}
                            {thin.map((p, k) => (
                                <text
                                    key={p.s.label}
                                    className="chart-side"
                                    x={x + barW + 5}
                                    y={thinY[k]}
                                    dy="0.32em"
                                    style={{ fill: p.s.color }}
                                >
                                    {format(p.v)}
                                </text>
                            ))}
                            <text className="chart-val" x={x + barW / 2} y={y(totals[i]) - 8} textAnchor="middle">
                                {format(totals[i])}
                            </text>
                            <text className="chart-axis" x={x + barW / 2} y={PAD.top + plotH + 18} textAnchor="middle">
                                <title>{cat}</title>
                                {/* '\n' no nome = duas linhas (ex.: mês em cima, ano embaixo). */}
                                {cat.split('\n').map((line, j) => (
                                    <tspan key={j} x={x + barW / 2} dy={j === 0 ? 0 : '1.2em'}>
                                        {short(line)}
                                    </tspan>
                                ))}
                            </text>
                            {/* Área de clique do tamanho da coluna toda (barra pequena também é clicável). */}
                            {(onSelect || tooltip) && (
                                <rect
                                    className={onSelect ? 'chart-hit' : 'chart-hit passive'}
                                    x={PAD.left + band * i}
                                    y={PAD.top}
                                    width={band}
                                    height={plotH + 24}
                                    role={onSelect ? 'button' : undefined}
                                    tabIndex={0}
                                    onMouseEnter={tooltip ? () => setHover(i) : undefined}
                                    onMouseLeave={tooltip ? () => setHover(null) : undefined}
                                    onFocus={tooltip ? () => setHover(i) : undefined}
                                    onBlur={tooltip ? () => setHover(null) : undefined}
                                    aria-label={`${selectLabel} ${cat} (${format(totals[i])})`}
                                    aria-pressed={onSelect ? selected.includes(cat) : undefined}
                                    onClick={onSelect ? () => onSelect(cat) : undefined}
                                    onKeyDown={(e) => {
                                        if (onSelect && (e.key === 'Enter' || e.key === ' ')) {
                                            e.preventDefault()
                                            onSelect(cat)
                                        }
                                    }}
                                />
                            )}
                        </g>
                    )
                })}
            </svg>
            {tooltip && hover !== null && (
                <ColumnTip
                    title={categories[hover]}
                    series={series}
                    index={hover}
                    total={totals[hover]}
                    format={format}
                    // Ao lado da coluna (à direita; à esquerda quando não cabe), na altura do topo do gráfico.
                    left={(() => {
                        const x = PAD.left + band * hover + (band - barW) / 2
                        return x + barW + 10 + TIP_W <= width ? x + barW + 10 : Math.max(0, x - 10 - TIP_W)
                    })()}
                    top={PAD.top}
                />
            )}
            {caption && <p className="chart-caption">{caption}</p>}
            {series.length > 1 && (
                <ul className="chart-legend" role="list">
                    {series.map((s) => (
                        <li key={s.label}>
                            <span className="chart-key" style={{ background: s.color }} />
                            {s.label}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}

type ColumnTipProps = {
    title: string
    series: ColumnSeries[]
    index: number
    total: number
    format: (v: number) => string
    left: number
    top: number
}

// A caixa do tooltip: o nome da coluna e o valor de cada parte, na ordem da legenda, com o total no fim.
function ColumnTip({ title, series, index, total, format, left, top }: ColumnTipProps) {
    return (
        <div className="chart-tip col-tip" role="status" style={{ left, top, width: TIP_W }}>
            <div className="chart-tip-head">
                <strong>{title}</strong>
            </div>
            {series.map((s) => (
                <div key={s.label} className="chart-tip-row">
                    <span className="chart-key dot" style={{ background: s.color }} />
                    <span>{s.label}</span>
                    <span className="num strong">{format(s.values[index] ?? 0)}</span>
                </div>
            ))}
            <div className="chart-tip-row chart-tip-total">
                <span />
                <span>Total</span>
                <span className="num strong">{format(total)}</span>
            </div>
        </div>
    )
}

// O que o gráfico mostra, em texto (leitor de tela).
function describe(categories: string[], series: ColumnSeries[], format: (v: number) => string): string {
    return categories
        .map((cat, i) => `${cat}: ${series.map((s) => `${s.label} ${format(s.values[i] ?? 0)}`).join(', ')}`)
        .join('; ')
}
