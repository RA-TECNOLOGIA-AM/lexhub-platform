import { fmt } from '../lib/format.ts'

type DeltaProps = {
    value: number | null
    betterWhenDown?: boolean
}

// Comparativo da v1: (atual - anterior) / anterior * 100.
// Verde ou vermelho depende do KPI: para tempo, cair é bom (betterWhenDown).
export function Delta({ value, betterWhenDown = false }: DeltaProps) {
    if (value === null) return null
    const good = betterWhenDown ? value < 0 : value > 0
    const arrow = value > 0 ? '▲' : value < 0 ? '▼' : '■'
    const className = value === 0 ? undefined : good ? 'delta-up' : 'delta-down'
    return (
        <>
            <span className={className}>
                {arrow} {fmt.pct(Math.abs(value))}
            </span>{' '}
            vs. mês anterior
        </>
    )
}