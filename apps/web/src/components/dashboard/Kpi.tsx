import type { ReactNode } from 'react'

type KpiProps = {
    label: string
    value: ReactNode
    note?: ReactNode
    tone?: 'danger' | 'warn' // destaca o valor: vermelho (ex.: atrasos) ou âmbar (ex.: fontes com falha)
}

// Cartão de indicador: rótulo, valor grande e uma nota opcional embaixo.
export function Kpi({ label, value, note, tone }: KpiProps) {
    return (
        <div className="card kpi">
            <span className="kpi-l">{label}</span>
            <span className={tone ? `kpi-v ${tone}` : 'kpi-v'}>{value}</span>
            {note && <span className="kpi-n">{note}</span>}
        </div>
    )
}
