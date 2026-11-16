import { fmt } from '../../lib/format.ts'
import { CountUp } from '../ui/CountUp.tsx'

type GaugeChartProps = {
    value: number // 0–100 (%)
    color: string // var(--...)
    caption?: string // embaixo do valor ("Meta: 85,0%")
    marker?: number // 0–100: risco da meta/limite no arco
    size?: number // largura em px
}

// Módulo: medidor em meia-lua (as "Taxas do período" da v1): o arco preenche até o valor, com o % no meio,
// a legenda embaixo e o risco da meta/limite. 0% à esquerda, 100% à direita.
export function GaugeChart({ value, color, caption, marker, size = 260 }: GaugeChartProps) {
    const v = Math.min(100, Math.max(0, value))
    const stroke = 30
    const r = size / 2 - stroke / 2 - 2
    const cx = size / 2
    const cy = size / 2 + 4
    const half = Math.PI * r // comprimento do arco inteiro (meia-volta)
    const arc = `M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`
    // Ponto do arco num % (0 = esquerda, 100 = direita), para o risco da meta.
    const at = (pct: number, radius: number) => {
        const a = Math.PI * (1 - pct / 100)
        return { x: cx + radius * Math.cos(a), y: cy - radius * Math.sin(a) }
    }
    const m = marker !== undefined ? [at(marker, r - stroke / 2 - 2), at(marker, r + stroke / 2 + 2)] : null
    const height = size / 2 + 12

    return (
        <div className="gauge-chart" style={{ width: size }}>
            <svg
                width={size}
                height={height}
                viewBox={`0 0 ${size} ${height}`}
                role="img"
                aria-label={`${fmt.dec1(v)}%${caption ? ` (${caption})` : ''}`}
            >
                <path className="gauge-track" d={arc} strokeWidth={stroke} />
                <path
                    className="gauge-fill"
                    d={arc}
                    strokeWidth={stroke}
                    style={{ stroke: color }}
                    strokeDasharray={`${(v / 100) * half} ${half}`}
                />
                {m && <line className="gauge-marker" x1={m[0].x} y1={m[0].y} x2={m[1].x} y2={m[1].y} />}
            </svg>
            <span className="gauge-center">
                <strong className="num">
                    <CountUp value={v} format={(x) => `${fmt.dec1(x)}%`} />
                </strong>
                {caption && <span>{caption}</span>}
            </span>
            <span className="gauge-scale num" aria-hidden="true">
                <span>0%</span>
                <span>100%</span>
            </span>
        </div>
    )
}
