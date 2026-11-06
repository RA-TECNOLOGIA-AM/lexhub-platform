import type { ReactNode } from 'react'

type KpiProps = {
    label: string
    value: ReactNode
    note?: ReactNode
}

// Cartão de indicador: rótulo, valor grande e uma nota opcional embaixo.
export function Kpi({ label, value, note }: KpiProps) {
    return (
        <div className="card kpi">
            <span className="kpi-l">{label}</span>
            <span className="kpi-v">{value}</span>
            {note && <span className="kpi-n">{note}</span>}
        </div>
    )
}