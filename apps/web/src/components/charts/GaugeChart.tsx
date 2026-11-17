import { fmt } from '../../lib/format.ts'
import { CountUp } from '../ui/CountUp.tsx'

type GaugeChartProps = {
    value: number // na escala de min a max (padrão: 0–100, em %)
    color: string // var(--...)
    caption?: string // embaixo do valor ("Meta: 85,0%")
    marker?: number // na mesma escala: risco da meta/limite no arco
    size?: number // largura em px
    min?: number // ponta esquerda (padrão 0)
    max?: number // ponta direita (padrão 100)
    format?: (v: number) => string // o número do meio e das pontas (padrão: "85,0%")
}

const pct = (x: number) => `${fmt.dec1(x)}%`

// Módulo: medidor em meia-lua (as "Taxas do período" da v1): o arco preenche até o valor, com o número no meio,
// a legenda embaixo e o risco da meta/limite. Padrão em %, de 0 (esquerda) a 100 (direita); com min/max/format,
// outra escala (ex.: a TRE da Execução, de -50 a 50 com 2 casas). Valor fora da escala enche até a ponta.
export function GaugeChart({
    value,
    color,
    caption,
    marker,
    size = 260,
    min = 0,
    max = 100,
    format = pct,
}: GaugeChartProps) {
    const span = max - min || 1
    const frac = (x: number) => Math.min(1, Math.max(0, (x - min) / span)) // 0 = esquerda, 1 = direita
    const v = frac(value)
    const stroke = 30
    const r = size / 2 - stroke / 2 - 2
    const cx = size / 2
    const cy = size / 2 + 4
    const half = Math.PI * r // comprimento do arco inteiro (meia-volta)
    const arc = `M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`
    // Ponto do arco numa fração (0 = esquerda, 1 = direita), para o risco da meta.
    const at = (f: number, radius: number) => {
        const a = Math.PI * (1 - f)
        return { x: cx + radius * Math.cos(a), y: cy - radius * Math.sin(a) }
    }
    const m = marker !== undefined ? [at(frac(marker), r - stroke / 2 - 2), at(frac(marker), r + stroke / 2 + 2)] : null
    const height = size / 2 + 12

    return (
        <div className="gauge-chart" style={{ width: size }}>
            <svg
                width={size}
                height={height}
                viewBox={`0 0 ${size} ${height}`}
                role="img"
                aria-label={`${format(value)}${caption ? ` (${caption})` : ''}`}
            >
                <path className="gauge-track" d={arc} strokeWidth={stroke} />
                <path
                    className="gauge-fill"
                    d={arc}
                    strokeWidth={stroke}
                    style={{ stroke: color }}
                    strokeDasharray={`${v * half} ${half}`}
                />
                {m && <line className="gauge-marker" x1={m[0].x} y1={m[0].y} x2={m[1].x} y2={m[1].y} />}
            </svg>
            <span className="gauge-center">
                <strong className="num">
                    <CountUp value={value} format={format} />
                </strong>
                {caption && <span>{caption}</span>}
            </span>
            <span className="gauge-scale num" aria-hidden="true">
                <span>{format(min)}</span>
                <span>{format(max)}</span>
            </span>
        </div>
    )
}
