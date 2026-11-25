import { useState } from 'react'
import { ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { fmt } from '../../../lib/format.ts'
import type { Point } from '../../../types/index.ts'

type RoscaLegendaProps = {
    items: Point[]
    centerLabel: string // embaixo do total, no meio ("clientes", "triados")
    selected?: string[]
    onSelect?: (name: string) => void
    selectLabel?: string
    format?: (v: number) => string // valor das fatias e da legenda (ex.: R$)
    centerFormat?: (v: number) => string // o total do meio, se diferente (ex.: R$ 77 mi, que cabe)
}

const cor = (k: number) => `var(--pie-${(k % 10) + 1})`

// Rosca com a legenda ao lado (nome, valor e %), como nos cards de Canal de aquisição e Gênero. Clicar numa fatia
// ou num item da legenda filtra a página; o cursor num item destaca a fatia dele.
export function RoscaLegenda({
    items,
    centerLabel,
    selected = [],
    onSelect,
    selectLabel,
    format = fmt.int,
    centerFormat,
}: RoscaLegendaProps) {
    const [hover, setHover] = useState<string | null>(null)
    const pts = [...items].filter((p) => p.value > 0).sort((a, b) => b.value - a.value)
    const total = pts.reduce((s, p) => s + p.value, 0)
    if (total === 0) return <ChartEmpty />
    const isSel = (name: string) => selected.some((s) => s.toUpperCase() === name.toUpperCase())

    return (
        <div className="mkt-rosca">
            <PieChart
                items={pts.map((p, k) => ({ ...p, color: cor(k) }))}
                sort={false}
                size={190}
                innerRatio={0.72}
                centerLabel={centerLabel}
                format={format}
                centerFormat={centerFormat}
                hover={hover}
                onHover={setHover}
                selected={selected}
                onSelect={onSelect}
                selectLabel={selectLabel}
            />
            <ul className="mkt-legenda" role="list">
                {pts.map((p, k) => (
                    <li
                        key={p.name}
                        className={
                            (selected.length > 0 && !isSel(p.name)) || (hover !== null && hover !== p.name)
                                ? 'dim'
                                : undefined
                        }
                    >
                        <button
                            type="button"
                            disabled={!onSelect}
                            aria-pressed={onSelect ? isSel(p.name) : undefined}
                            aria-label={onSelect ? `${selectLabel ?? 'Filtrar por'} ${p.name}` : undefined}
                            onClick={() => onSelect?.(p.name)}
                            onMouseEnter={() => setHover(p.name)}
                            onMouseLeave={() => setHover(null)}
                            onFocus={() => setHover(p.name)}
                            onBlur={() => setHover(null)}
                        >
                            <span className="chart-key" style={{ background: cor(k) }} />
                            <span className="mkt-legenda-nome">{p.name}</span>
                            <span className="num">
                                <strong>{format(p.value)}</strong>{' '}
                                <span className="muted">({fmt.dec1((p.value / total) * 100)}%)</span>
                            </span>
                        </button>
                    </li>
                ))}
            </ul>
        </div>
    )
}
