import { useState } from 'react'
import { fmt } from '../../lib/format.ts'
import { ChartEmpty } from './ChartCard.tsx'
import { PieChart } from './PieChart.tsx'

export type DonutSlice = { label: string; value: number; color: string } // color = var(--...)

type DonutChartProps = {
    slices: DonutSlice[]
    centerLabel?: string // embaixo do total, no meio da rosca
    size?: number
}

// Módulo: rosca com o total no meio e a legenda (valor e %) ao lado (Taxa de resolvidos). A rosca é a pizza
// padrão (PieChart), com a mesma animação: a fatia do cursor sai do lugar, as outras apagam e o meio mostra o
// valor dela. Passar o cursor num item da legenda destaca a fatia dele.
export function DonutChart({ slices, centerLabel, size = 200 }: DonutChartProps) {
    const [hover, setHover] = useState<string | null>(null)
    const total = slices.reduce((sum, s) => sum + s.value, 0)
    if (total === 0) return <ChartEmpty />

    const share = (v: number) => (v / total) * 100
    return (
        <div className="donut">
            <PieChart
                items={slices.map((s) => ({ name: s.label, value: s.value, color: s.color }))}
                size={size}
                sort={false}
                innerRatio={0.74}
                centerLabel={centerLabel}
                hover={hover}
                onHover={setHover}
            />
            <ul className="donut-legend" role="list">
                {slices.map((s) => (
                    <li
                        key={s.label}
                        className={hover === null ? undefined : hover === s.label ? 'on' : 'dim'}
                        onMouseEnter={() => s.value > 0 && setHover(s.label)}
                        onMouseLeave={() => setHover(null)}
                    >
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
