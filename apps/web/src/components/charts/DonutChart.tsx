import { CountUp } from '../ui/CountUp.tsx'
import { fmt } from '../../lib/format.ts'
import { ChartEmpty } from './ChartCard.tsx'

export type DonutSlice = { label: string; value: number; color: string } // color = var(--...)

type DonutChartProps = {
    slices: DonutSlice[]
    centerLabel?: string // embaixo do total, no meio da rosca
    size?: number
}

// Módulo: rosca com o total no meio e a legenda (valor e %) ao lado (Taxa de resolvidos).
export function DonutChart({ slices, centerLabel, size = 200 }: DonutChartProps) {
    const total = slices.reduce((sum, s) => sum + s.value, 0)
    if (total === 0) return <ChartEmpty />

    const share = (v: number) => (v / total) * 100
    const r = size / 2 - 14
    const c = 2 * Math.PI * r
    const gap = slices.filter((s) => s.value > 0).length > 1 ? 3 : 0 // fresta entre as fatias
    // Onde cada fatia começa (soma das anteriores), calculado antes do desenho.
    const starts = slices.map((_, i) => slices.slice(0, i).reduce((sum, x) => sum + (x.value / total) * c, 0))
    const describe = slices.map((s) => `${s.label}: ${fmt.int(s.value)} (${fmt.dec1(share(s.value))}%)`)

    return (
        <div className="donut">
            <div className="donut-ring" style={{ width: size, height: size }}>
                <svg
                    width={size}
                    height={size}
                    viewBox={`0 0 ${size} ${size}`}
                    role="img"
                    aria-label={describe.join('; ')}
                >
                    <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
                        <circle className="donut-track" cx={size / 2} cy={size / 2} r={r} />
                        {slices.map((s, i) => {
                            const dash = Math.max((s.value / total) * c - gap, 0)
                            return (
                                <circle
                                    key={s.label}
                                    className="donut-slice"
                                    cx={size / 2}
                                    cy={size / 2}
                                    r={r}
                                    style={{ stroke: s.color }}
                                    strokeDasharray={`${dash} ${c - dash}`}
                                    strokeDashoffset={-starts[i]}
                                />
                            )
                        })}
                    </g>
                </svg>
                <span className="donut-center">
                    <strong className="num">
                        <CountUp value={total} format={fmt.int} />
                    </strong>
                    {centerLabel && <span>{centerLabel}</span>}
                </span>
            </div>
            <ul className="donut-legend" role="list">
                {slices.map((s) => (
                    <li key={s.label}>
                        <span className="chart-key" style={{ background: s.color }} />
                        <span className="donut-legend-l">{s.label}</span>
                        <strong className="num">{fmt.int(s.value)}</strong>
                        <span className="num muted">{fmt.dec1(share(s.value))}%</span>
                    </li>
                ))}
            </ul>
        </div>
    )
}
