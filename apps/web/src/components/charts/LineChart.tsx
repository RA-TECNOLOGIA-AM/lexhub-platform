import { useId, useState, type KeyboardEvent, type MouseEvent } from 'react'
import { niceScale, smoothPath, type XY } from '../../lib/charts.ts'
import { fmt } from '../../lib/format.ts'
import { ChartEmpty } from './ChartCard.tsx'
import { useWidth } from './useWidth.ts'

export type LineSeries = {
    label: string
    color: string
    values: (number | null)[] // null = sem dado no ponto
    dashed?: boolean // linha tracejada (ex.: anos anteriores no "mês a mês")
    area?: boolean // degradê embaixo só desta série (vale mais que o `area` do gráfico)
}

type LineChartProps = {
    labels: string[] // eixo x
    series: LineSeries[]
    height?: number
    format?: (v: number) => string
    legend?: boolean // legenda embaixo (ex.: um ano por linha)
    area?: boolean // preenchimento em degradê embaixo da linha
    reference?: { value: number; label: string } // linha tracejada horizontal (ex.: meta diária)
    partial?: { series: number; index: number } // ponto ainda em andamento (ex.: o mês atual): "parcial"
    emphasizeData?: boolean // rótulo do eixo em negrito onde há dado
    tooltip?: { heading: string; title: (i: number) => string } // caixa ao passar o cursor ("Mês" · "Abril")
}

const PAD = { top: 30, right: 40, bottom: 36, left: 52 }

// Módulo: linhas suaves com o valor em cada ponto (Produção diária, Protocolados mês a mês).
// Mês sem dado corta a linha (não liga setembro a novembro passando por cima de outubro).
// Cursor (ou setas do teclado, com o gráfico em foco) mostra a caixa com os valores do ponto.
export function LineChart({
    labels,
    series,
    height = 300,
    format = fmt.int,
    legend = false,
    area = false,
    reference,
    partial,
    emphasizeData = false,
    tooltip,
}: LineChartProps) {
    const [ref, width] = useWidth<HTMLDivElement>()
    const [hover, setHover] = useState<number | null>(null)
    const gradId = useId()
    const all = series.flatMap((s) => s.values.filter((v): v is number => v !== null))
    if (labels.length === 0 || all.length === 0) {
        return (
            <div ref={ref}>
                <ChartEmpty />
            </div>
        )
    }

    const { max, ticks } = niceScale(Math.max(...all, reference?.value ?? 0))
    // Margem do eixo do tamanho do maior rótulo (ex.: '800 mil'), para não cortar.
    const padLeft = Math.max(PAD.left, Math.max(...ticks.map((t) => fmt.eixo(t).length)) * 7 + 16)
    const plotW = Math.max(width - padLeft - PAD.right, 40)
    const plotH = height - PAD.top - PAD.bottom
    const base = PAD.top + plotH
    const step = labels.length > 1 ? plotW / (labels.length - 1) : 0
    const x = (i: number) => padLeft + (labels.length > 1 ? step * i : plotW / 2)
    const y = (v: number) => base - (v / max) * plotH
    // Rótulos do eixo x sem encavalar: o espaço de um rótulo depende do maior texto ('jan' cabe mais junto
    // que 'setembro'); onde não há rótulo, o ponto também fica sem o número.
    const maior = Math.max(...labels.map((l) => l.length))
    const gap = Math.max(40, maior * 7.5 + 14)
    const every = Math.max(1, Math.ceil(gap / Math.max(step, 1)))
    // O último ponto sempre tem rótulo; se ficar colado no rótulo regular anterior, este some no lugar dele.
    const ultimo = labels.length - 1
    const ultimoRegular = Math.floor(ultimo / every) * every
    const colado = ultimo !== ultimoRegular && (ultimo - ultimoRegular) * step < gap
    const comRotulo = (i: number) => i === ultimo || (i % every === 0 && !(colado && i === ultimoRegular))
    const hasData = labels.map((_, i) => series.some((s) => s.values[i] !== null && s.values[i] !== undefined))

    const indexAt = (clientX: number, el: Element) => {
        const left = el.getBoundingClientRect().left
        const i = Math.round((clientX - left - padLeft) / (step || 1))
        return Math.min(labels.length - 1, Math.max(0, i))
    }
    const onMove = (e: MouseEvent<SVGSVGElement>) => setHover(indexAt(e.clientX, e.currentTarget))
    const onKey = (e: KeyboardEvent<SVGSVGElement>) => {
        if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
        e.preventDefault()
        const d = e.key === 'ArrowLeft' ? -1 : 1
        setHover((h) => Math.min(labels.length - 1, Math.max(0, (h ?? (d > 0 ? -1 : labels.length)) + d)))
    }
    const interactive = tooltip !== undefined

    return (
        <div ref={ref} className="chart-svg line-wrap">
            <svg
                width={width}
                height={height}
                role="img"
                aria-label={describe(labels, series, format)}
                tabIndex={interactive ? 0 : undefined}
                onMouseMove={interactive ? onMove : undefined}
                onMouseLeave={interactive ? () => setHover(null) : undefined}
                onKeyDown={interactive ? onKey : undefined}
                onBlur={interactive ? () => setHover(null) : undefined}
            >
                <defs>
                    {series.map((s, k) => (
                        <linearGradient key={s.label} id={`${gradId}-${k}`} x1="0" x2="0" y1="0" y2="1">
                            <stop offset="0%" style={{ stopColor: s.color, stopOpacity: 0.35 }} />
                            <stop offset="100%" style={{ stopColor: s.color, stopOpacity: 0 }} />
                        </linearGradient>
                    ))}
                </defs>
                {ticks.map((t) => (
                    <g key={t}>
                        <line className="chart-grid" x1={padLeft} x2={padLeft + plotW} y1={y(t)} y2={y(t)} />
                        <text className="chart-axis" x={padLeft - 10} y={y(t)} dy="0.32em" textAnchor="end">
                            {fmt.eixo(t)}
                        </text>
                    </g>
                ))}
                <line className="chart-baseline" x1={padLeft} x2={padLeft + plotW} y1={base} y2={base} />
                {labels.map((l, i) =>
                    comRotulo(i) ? (
                        <g key={l}>
                            <line className="chart-grid" x1={x(i)} x2={x(i)} y1={PAD.top} y2={base} />
                            <text
                                className={emphasizeData && hasData[i] ? 'chart-axis strong' : 'chart-axis'}
                                x={x(i)}
                                y={base + 22}
                                textAnchor="middle"
                            >
                                {l}
                            </text>
                        </g>
                    ) : null,
                )}
                {reference && (
                    <g className="chart-ref">
                        <line x1={padLeft} x2={padLeft + plotW} y1={y(reference.value)} y2={y(reference.value)} />
                        <text x={padLeft + plotW} y={y(reference.value) - 7} textAnchor="end">
                            {reference.label}
                        </text>
                    </g>
                )}
                {hover !== null && (
                    <line className="chart-cursor" x1={x(hover)} x2={x(hover)} y1={PAD.top - 10} y2={base} />
                )}
                {series.map((s, k) => (
                    <g key={s.label} style={{ color: s.color }}>
                        {segments(s.values).map((seg) => {
                            const pts = seg.map(({ i, v }): XY => ({ x: x(i), y: y(v) }))
                            const d = smoothPath(pts)
                            return (
                                <g key={seg[0].i}>
                                    {(s.area ?? area) && pts.length > 1 && (
                                        <path
                                            d={`${d}L${pts[pts.length - 1].x},${base}L${pts[0].x},${base}Z`}
                                            fill={`url(#${gradId}-${k})`}
                                        />
                                    )}
                                    <path className={s.dashed ? 'chart-line dashed' : 'chart-line'} d={d} />
                                </g>
                            )
                        })}
                        {/* Valor só na última série (o ano mais recente) e, com muitos pontos, só onde há rótulo no eixo. */}
                        {s.values.map((v, i) => {
                            if (v === null) return null
                            const isPartial = partial?.series === k && partial.index === i
                            return (
                                <g key={i}>
                                    {isPartial && <circle className="chart-halo" cx={x(i)} cy={y(v)} r={11} />}
                                    <circle
                                        className={hover === i ? 'chart-dot on' : 'chart-dot'}
                                        cx={x(i)}
                                        cy={y(v)}
                                        r={hover === i ? 6 : 5}
                                    />
                                    {k === series.length - 1 && comRotulo(i) && (
                                        <text className="chart-val" x={x(i)} y={y(v) - 13} textAnchor="middle">
                                            {format(v)}
                                        </text>
                                    )}
                                    {isPartial && (
                                        // "parcial" embaixo do ponto; perto do eixo (ia cobrir o mês), em cima do valor
                                        <text
                                            className="chart-partial"
                                            x={x(i)}
                                            y={y(v) + 26 <= base - 8 ? y(v) + 26 : y(v) - 32}
                                            textAnchor="middle"
                                        >
                                            parcial
                                        </text>
                                    )}
                                </g>
                            )
                        })}
                    </g>
                ))}
            </svg>
            {tooltip && hover !== null && (
                <div
                    className="chart-tip"
                    role="status"
                    style={{
                        left: Math.min(Math.max(x(hover), 90), width - 90),
                        top: Math.max(PAD.top - 20, 0),
                    }}
                >
                    <div className="chart-tip-head">
                        <span>{tooltip.heading}</span>
                        <strong>{tooltip.title(hover)}</strong>
                    </div>
                    {series.map((s) => {
                        const v = s.values[hover]
                        return (
                            <div key={s.label} className="chart-tip-row">
                                <span className="chart-key dot" style={{ background: s.color }} />
                                <span className="num">{s.label}</span>
                                <span className={v === null || v === undefined ? 'muted num' : 'num strong'}>
                                    {v === null || v === undefined ? 'Sem registro' : format(v)}
                                </span>
                            </div>
                        )
                    })}
                </div>
            )}
            {legend && (
                <ul className="chart-legend" role="list">
                    {series.map((s) => (
                        <li key={s.label}>
                            <span
                                className={s.dashed ? 'chart-key line dashed' : 'chart-key line'}
                                style={s.dashed ? { color: s.color } : { background: s.color }}
                            />
                            {s.label}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}

// Trechos contínuos (sem null) de uma série.
function segments(values: (number | null)[]): { i: number; v: number }[][] {
    const out: { i: number; v: number }[][] = []
    let current: { i: number; v: number }[] = []
    values.forEach((v, i) => {
        if (v === null) {
            if (current.length) out.push(current)
            current = []
        } else current.push({ i, v })
    })
    if (current.length) out.push(current)
    return out
}

function describe(labels: string[], series: LineSeries[], format: (v: number) => string): string {
    return series
        .map(
            (s) =>
                `${s.label}: ` +
                s.values
                    .map((v, i) => (v === null ? null : `${labels[i]} ${format(v)}`))
                    .filter(Boolean)
                    .join(', '),
        )
        .join('; ')
}
