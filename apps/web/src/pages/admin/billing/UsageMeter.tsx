import { usagePct, usageTone } from './billingView.ts'

type UsageMeterProps = {
    label: string // nome acessível da barra ("Assentos", "Assentos de LexGroup")
    used: number
    total: number | null // null = sem teto: não desenha a barra
}

// Módulo: a barra de uso de um limite do plano. Usada em Plano e cobrança e em Clientes.
export function UsageMeter({ label, used, total }: UsageMeterProps) {
    if (total === null) return null
    return (
        <div
            className="usage-track"
            role="meter"
            aria-label={label}
            aria-valuemin={0}
            aria-valuemax={total}
            aria-valuenow={used}
        >
            <div className={`usage-fill ${usageTone(used, total)}`} style={{ width: `${usagePct(used, total)}%` }} />
        </div>
    )
}
