import type { CSSProperties } from 'react'
import { fmt } from '../../lib/format.ts'
import { ChartEmpty } from './ChartCard.tsx'

export type StackedPart = { label: string; color: string } // color = var(--...)

type StackedBarsProps = {
    rows: { name: string; values: number[] }[] // um valor por parte, na ordem de `parts`
    parts: StackedPart[]
    format?: (v: number) => string
    selected?: string[]
    onSelect?: (name: string) => void
    selectLabel?: string
    showTotal?: boolean // total da linha ao lado do nome (false: só os valores de cada parte)
}

// Módulo: barras horizontais empilhadas por linha (ex.: Valor de causa por atendente = Protocolado + Não protocolado).
// Cada barra vai até o total da linha, proporcional ao maior total; os valores de cada parte ficam na legenda da linha.
export function StackedBars({
    rows,
    parts,
    format = fmt.int,
    selected = [],
    onSelect,
    selectLabel = 'Filtrar por',
    showTotal = true,
}: StackedBarsProps) {
    const totals = rows.map((r) => r.values.reduce((sum, v) => sum + v, 0))
    const top = Math.max(0, ...totals)
    if (rows.length === 0 || top === 0) return <ChartEmpty />

    return (
        <div className="stacked">
            <ul className="stacked-list" role="list">
                {rows.map((r, i) => {
                    const active = selected.includes(r.name)
                    const body = (
                        <>
                            <span className="stacked-head">
                                <strong>{r.name}</strong>
                                {showTotal && <span className="num">{format(totals[i])}</span>}
                            </span>
                            <span
                                className="stacked-track"
                                aria-hidden="true"
                                style={{ '--w': `${(totals[i] / top) * 100}%` } as CSSProperties}
                            >
                                {r.values.map((v, k) =>
                                    v > 0 ? (
                                        <span
                                            key={parts[k].label}
                                            style={{ flexGrow: v, background: parts[k].color }}
                                        />
                                    ) : null,
                                )}
                            </span>
                            <span className="stacked-values num">
                                {parts.map((p, k) => (
                                    <span key={p.label}>
                                        <span className="chart-key dot" style={{ background: p.color }} />
                                        {format(r.values[k] ?? 0)}
                                    </span>
                                ))}
                            </span>
                        </>
                    )
                    return (
                        <li key={r.name} className={selected.length > 0 && !active ? 'dim' : undefined}>
                            {onSelect ? (
                                <button
                                    type="button"
                                    className="stacked-row"
                                    aria-pressed={active}
                                    aria-label={`${selectLabel} ${r.name} (${format(totals[i])})`}
                                    onClick={() => onSelect(r.name)}
                                >
                                    {body}
                                </button>
                            ) : (
                                <div className="stacked-row">{body}</div>
                            )}
                        </li>
                    )
                })}
            </ul>
            <ul className="chart-legend" role="list">
                {parts.map((p) => (
                    <li key={p.label}>
                        <span className="chart-key" style={{ background: p.color }} />
                        {p.label}
                    </li>
                ))}
            </ul>
        </div>
    )
}
