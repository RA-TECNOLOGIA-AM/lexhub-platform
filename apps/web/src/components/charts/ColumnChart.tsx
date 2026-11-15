import { niceScale } from '../../lib/charts.ts'
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
}

const PAD = { top: 26, right: 12, bottom: 44, left: 40 }

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
}: ColumnChartProps) {
    const [ref, width] = useWidth<HTMLDivElement>()
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
        <div ref={ref} className={className ? `chart-svg ${className}` : 'chart-svg'}>
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
                                        {series.length > 1 && k === 0 && y0 - y1 > 18 && (
                                            <text className="chart-in" x={x + barW / 2} y={(y0 + y1) / 2} dy="0.32em">
                                                {format(v)}
                                            </text>
                                        )}
                                    </g>
                                ) : null,
                            )}
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
                            {onSelect && (
                                <rect
                                    className="chart-hit"
                                    x={PAD.left + band * i}
                                    y={PAD.top}
                                    width={band}
                                    height={plotH + 24}
                                    role="button"
                                    tabIndex={0}
                                    aria-label={`${selectLabel} ${cat} (${format(totals[i])})`}
                                    aria-pressed={selected.includes(cat)}
                                    onClick={() => onSelect(cat)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' || e.key === ' ') {
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

// O que o gráfico mostra, em texto (leitor de tela).
function describe(categories: string[], series: ColumnSeries[], format: (v: number) => string): string {
    return categories
        .map((cat, i) => `${cat}: ${series.map((s) => `${s.label} ${format(s.values[i] ?? 0)}`).join(', ')}`)
        .join('; ')
}
