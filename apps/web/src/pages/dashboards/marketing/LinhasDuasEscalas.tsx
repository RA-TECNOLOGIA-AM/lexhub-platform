import { useState, type KeyboardEvent, type MouseEvent } from 'react'
import { ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { useWidth } from '../../../components/charts/useWidth.ts'
import { niceScale } from '../../../lib/charts.ts'
import { fmt } from '../../../lib/format.ts'

type Serie = { label: string; color: string; values: number[] }

type Props = {
    labels: string[] // eixo x (dias)
    esquerda: Serie // escala do eixo da esquerda (ex.: cliques)
    direita: Serie // escala do eixo da direita (ex.: leads, bem menores)
    height?: number
    heading?: string // título da caixa do cursor ("Dia")
}

const PAD = { top: 16, right: 44, bottom: 30, left: 48 }
const MAX_ROTULOS_X = 9

// Duas linhas com escalas próprias (eixo esquerdo e direito), para comparar o desenho de séries de tamanhos
// diferentes (cliques na casa das centenas, leads na das dezenas). Cursor (ou setas) mostra os valores do dia.
export function LinhasDuasEscalas({ labels, esquerda, direita, height = 260, heading = 'Dia' }: Props) {
    const [ref, width] = useWidth<HTMLDivElement>()
    const [hover, setHover] = useState<number | null>(null)
    const n = labels.length
    if (n === 0 || [...esquerda.values, ...direita.values].every((v) => v === 0)) {
        return (
            <div ref={ref}>
                <ChartEmpty />
            </div>
        )
    }

    const escE = niceScale(Math.max(...esquerda.values))
    const escD = niceScale(Math.max(...direita.values))
    const w = Math.max(width, 280)
    const plotW = w - PAD.left - PAD.right
    const plotH = height - PAD.top - PAD.bottom
    const x = (i: number) => PAD.left + (n === 1 ? plotW / 2 : (i / (n - 1)) * plotW)
    const yE = (v: number) => PAD.top + plotH - (v / escE.max) * plotH
    const yD = (v: number) => PAD.top + plotH - (v / escD.max) * plotH
    const linha = (vals: number[], y: (v: number) => number) =>
        vals.map((v, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join('')
    const passo = Math.max(1, Math.ceil(n / MAX_ROTULOS_X))
    const rotulosX = labels.map((l, i) => ({ l, i })).filter(({ i }) => i % passo === 0 || i === n - 1)

    const indice = (clientX: number, el: Element) => {
        const box = el.getBoundingClientRect()
        const rel = ((clientX - box.left) / box.width) * w - PAD.left
        return Math.min(n - 1, Math.max(0, Math.round((rel / plotW) * (n - 1))))
    }
    const onMove = (e: MouseEvent<SVGSVGElement>) => setHover(indice(e.clientX, e.currentTarget))
    const onKey = (e: KeyboardEvent<SVGSVGElement>) => {
        if (e.key === 'ArrowRight') setHover((h) => Math.min(n - 1, (h ?? -1) + 1))
        else if (e.key === 'ArrowLeft') setHover((h) => Math.max(0, (h ?? n) - 1))
        else return
        e.preventDefault()
    }

    const caixaEsquerda = hover !== null && x(hover) > w / 2

    return (
        <div ref={ref} className="mkt-duas">
            <svg
                width={w}
                height={height}
                viewBox={`0 0 ${w} ${height}`}
                role="img"
                aria-label={`${esquerda.label} (eixo esquerdo) e ${direita.label} (eixo direito) por ${heading.toLowerCase()}`}
                tabIndex={0}
                onMouseMove={onMove}
                onMouseLeave={() => setHover(null)}
                onKeyDown={onKey}
                onBlur={() => setHover(null)}
            >
                {escE.ticks.map((t, k) => (
                    <g key={t}>
                        <line className="mkt-duas-grade" x1={PAD.left} x2={w - PAD.right} y1={yE(t)} y2={yE(t)} />
                        <text className="mkt-duas-eixo" x={PAD.left - 8} y={yE(t) + 4} textAnchor="end">
                            {fmt.eixo(t)}
                        </text>
                        {escD.ticks[k] !== undefined && (
                            <text
                                className="mkt-duas-eixo"
                                x={w - PAD.right + 8}
                                y={yD(escD.ticks[k]) + 4}
                                fill={direita.color}
                            >
                                {fmt.eixo(escD.ticks[k])}
                            </text>
                        )}
                    </g>
                ))}
                {rotulosX.map(({ l, i }) => (
                    <text key={i} className="mkt-duas-eixo" x={x(i)} y={height - 8} textAnchor="middle">
                        {l}
                    </text>
                ))}
                {hover !== null && (
                    <line className="mkt-duas-cursor" x1={x(hover)} x2={x(hover)} y1={PAD.top} y2={PAD.top + plotH} />
                )}
                {[
                    { s: esquerda, y: yE },
                    { s: direita, y: yD },
                ].map(({ s, y }) => (
                    <g key={s.label}>
                        <path d={linha(s.values, y)} fill="none" stroke={s.color} strokeWidth={2} />
                        {s.values.map((v, i) => (
                            <circle
                                key={i}
                                cx={x(i)}
                                cy={y(v)}
                                r={hover === i ? 5 : 2.5}
                                fill={hover === i ? s.color : 'var(--surface)'}
                                stroke={s.color}
                                strokeWidth={1.5}
                            />
                        ))}
                    </g>
                ))}
            </svg>
            {hover !== null && (
                <div
                    className="mkt-duas-caixa"
                    style={
                        caixaEsquerda
                            ? { right: w - x(hover) + 12, top: PAD.top }
                            : { left: x(hover) + 12, top: PAD.top }
                    }
                >
                    <span className="mkt-duas-caixa-t">
                        {heading} <strong className="num">{labels[hover]}</strong>
                    </span>
                    {[esquerda, direita].map((s) => (
                        <span key={s.label} className="mkt-duas-caixa-l" style={{ color: s.color }}>
                            <span>{s.label}:</span>
                            <strong className="num">{fmt.int(s.values[hover])}</strong>
                        </span>
                    ))}
                </div>
            )}
        </div>
    )
}
