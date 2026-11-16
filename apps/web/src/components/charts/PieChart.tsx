import { useState } from 'react'
import { arcPath, pieSlices, spreadColumn } from '../../lib/charts.ts'
import { fmt } from '../../lib/format.ts'
import { CountUp } from '../ui/CountUp.tsx'
import { ChartEmpty } from './ChartCard.tsx'
import { useWidth } from './useWidth.ts'

type PieChartProps = {
    items: { name: string; value: number; color?: string }[] // color: cor fixa da fatia (senão, a paleta)
    max?: number // fatias com cor própria; passando disso, o resto vira "Outras" (padrão: todas)
    size?: number
    format?: (v: number) => string
    centerLabel?: string // embaixo do total, no meio da rosca
    selected?: string[]
    onSelect?: (name: string) => void
    selectLabel?: string
    labels?: boolean // nome, valor e % de cada fatia em volta da rosca (some quando não há largura)
    sort?: boolean // fatias da maior para a menor (padrão); false mantém a ordem de `items`
    innerRatio?: number // raio do furo / raio da rosca
    hover?: string | null // fatia em destaque controlada de fora (ex.: pela legenda ao lado)
    onHover?: (name: string | null) => void
}

const PALETTE = 10 // cores --pie-1 … --pie-10 (app.css), em ciclo
const color = (k: number) => `var(--pie-${(k % PALETTE) + 1})`
const REST = 'var(--pie-rest)'
const POP = 8 // quanto a fatia em destaque sai do lugar (px)
const LABEL_GAP = 16 // distância mínima entre dois rótulos do mesmo lado
const CHAR_W = 6.6 // largura média (px) de um caractere do rótulo (12px), para saber se os rótulos cabem

// Módulo: o gráfico de pizza padrão, em rosca (Distribuição por rubrica; a Taxa de resolvidos usa por baixo). O meio mostra o total;
// com o cursor (ou o foco) numa fatia, ela sai um pouco do lugar, as outras apagam e o meio mostra o nome, o
// valor e o %. Clicar numa fatia filtra (onSelect); com filtro ativo, só as escolhidas ficam acesas. Com
// `labels`, cada fatia tem o rótulo (nome, valor e %) em volta, ligado por uma linha na cor dela.
export function PieChart({
    items,
    max = Infinity,
    size = 320,
    format = fmt.int,
    centerLabel,
    selected = [],
    onSelect,
    selectLabel = 'Filtrar por',
    labels = false,
    sort = true,
    innerRatio = 0.62,
    hover: hoverProp,
    onHover,
}: PieChartProps) {
    const [ref, width] = useWidth<HTMLDivElement>()
    const [hoverLocal, setHoverLocal] = useState<string | null>(null)
    const hover = hoverProp !== undefined ? hoverProp : hoverLocal
    const setHover = (name: string | null) => {
        setHoverLocal(name)
        onHover?.(name)
    }
    const slices = pieSlices(items, max, 'Outras', sort)
    if (slices.length === 0) {
        return (
            <div ref={ref}>
                <ChartEmpty />
            </div>
        )
    }

    const total = slices.reduce((sum, s) => sum + s.value, 0)
    const isSel = (name: string) => selected.some((s) => s.toUpperCase() === name.toUpperCase())
    const atual = slices.find((s) => s.name === hover)
    const r = size / 2 - POP - 2
    const inner = r * innerRatio
    const fixed = new Map(items.map((p) => [p.name, p.color]))
    const fill = (name: string, k: number, others: number) => (others ? REST : (fixed.get(name) ?? color(k)))
    // Cabem os rótulos? O mais comprido de cada lado ('NOME 65 (11,8%)') + a folga até a rosca.
    const rotulo = (s: (typeof slices)[number]) => `${s.name} ${format(s.value)} (${fmt.dec1(s.share)}%)`.length
    const labelRoom = Math.max(0, ...slices.map(rotulo)) * CHAR_W + 40
    const comRotulos = labels && width >= size + 2 * labelRoom
    // Rótulos de cada lado (direita: metade da direita da volta), espalhados para não se encostarem.
    const angle = (f: number) => f * 2 * Math.PI - Math.PI / 2
    const mids = slices.map((s) => angle((s.start + s.end) / 2))
    const right = mids.map((a) => Math.cos(a) >= 0)
    const perSide = Math.max(right.filter(Boolean).length, right.filter((x) => !x).length)
    const h = comRotulos ? Math.max(size + 48, perSide * LABEL_GAP + 24) : size
    const w = comRotulos ? width : size
    const cx = w / 2
    const cy = h / 2
    const rotR = r + 14 // raio onde os rótulos encostam na rosca
    const labelY = new Array<number>(slices.length)
    if (comRotulos) {
        for (const lado of [true, false]) {
            const idx = slices.map((_, i) => i).filter((i) => right[i] === lado)
            const ys = spreadColumn(
                idx.map((i) => cy + rotR * Math.sin(mids[i])),
                LABEL_GAP,
                10,
                h - 10,
            )
            idx.forEach((i, k) => (labelY[i] = ys[k]))
        }
    }
    const hoverProps = (name: string) => ({
        onMouseEnter: () => setHover(name),
        onMouseLeave: () => setHover(null),
    })

    return (
        <div ref={ref} className="pie">
            <div className="pie-figure" style={{ width: comRotulos ? '100%' : size, height: h }}>
                <svg
                    width={w}
                    height={h}
                    viewBox={`0 0 ${w} ${h}`}
                    role="group"
                    aria-label={slices.map((s) => `${s.name}: ${format(s.value)} (${fmt.dec1(s.share)}%)`).join('; ')}
                >
                    {slices.map((s, k) => {
                        const mid = mids[k]
                        const on = hover === s.name || (hover === null && !s.others && isSel(s.name))
                        const dim = hover !== null ? hover !== s.name : selected.length > 0 && !isSel(s.name)
                        const pop = on ? POP : 0
                        const clickable = onSelect !== undefined && !s.others
                        return (
                            <path
                                key={s.name}
                                className={`pie-slice${dim ? ' dim' : ''}${clickable ? ' clickable' : ''}`}
                                d={arcPath(cx, cy, r, s.start, s.end, inner)}
                                transform={`translate(${(Math.cos(mid) * pop).toFixed(2)} ${(Math.sin(mid) * pop).toFixed(2)})`}
                                style={{ fill: fill(s.name, k, s.others) }}
                                role={clickable ? 'button' : undefined}
                                tabIndex={0}
                                aria-label={`${clickable ? `${selectLabel} ` : ''}${s.name}: ${format(s.value)} (${fmt.dec1(s.share)}%)`}
                                aria-pressed={clickable ? isSel(s.name) : undefined}
                                {...hoverProps(s.name)}
                                onFocus={() => setHover(s.name)}
                                onBlur={() => setHover(null)}
                                onClick={clickable ? () => onSelect(s.name) : undefined}
                                onKeyDown={(e) => {
                                    if (clickable && (e.key === 'Enter' || e.key === ' ')) {
                                        e.preventDefault()
                                        onSelect(s.name)
                                    }
                                }}
                            />
                        )
                    })}
                    {comRotulos &&
                        slices.map((s, k) => {
                            const lado = right[k] ? 1 : -1
                            const a = mids[k]
                            const ponta = (rad: number) => [cx + rad * Math.cos(a), cy + rad * Math.sin(a)]
                            const [x0, y0] = ponta(r + 2)
                            // O rótulo segue a volta da rosca (saindo da fatia); afastado dos vizinhos, desliza
                            // na mesma curva e uma linha curta liga à fatia.
                            const dy = labelY[k] - cy
                            const xt = cx + lado * (Math.sqrt(Math.max(rotR * rotR - dy * dy, 0)) + 6)
                            const longe = Math.hypot(xt - x0, labelY[k] - y0) > 18
                            const dim = hover !== null ? hover !== s.name : selected.length > 0 && !isSel(s.name)
                            return (
                                <g
                                    key={s.name}
                                    className={`pie-label${dim ? ' dim' : ''}`}
                                    {...hoverProps(s.name)}
                                    onClick={onSelect && !s.others ? () => onSelect(s.name) : undefined}
                                    aria-hidden="true"
                                >
                                    {longe && (
                                        <polyline
                                            points={`${x0},${y0} ${xt - lado * 4},${labelY[k]}`}
                                            style={{ stroke: fill(s.name, k, s.others) }}
                                        />
                                    )}
                                    <text x={xt} y={labelY[k]} dy="0.32em" textAnchor={lado > 0 ? 'start' : 'end'}>
                                        {s.name}
                                        {s.others ? ` (${s.others})` : ''}{' '}
                                        <tspan className="pie-label-v">
                                            {format(s.value)} ({fmt.dec1(s.share)}%)
                                        </tspan>
                                    </text>
                                </g>
                            )
                        })}
                </svg>
                <span className="pie-center" aria-live="polite" style={{ width: inner * 1.6 }}>
                    {atual ? (
                        <>
                            <span className="pie-center-name" title={atual.name}>
                                {atual.name}
                                {atual.others ? ` (${atual.others})` : ''}
                            </span>
                            <strong className="num">{format(atual.value)}</strong>
                            <span className="num">{fmt.dec1(atual.share)}%</span>
                        </>
                    ) : (
                        <>
                            <strong className="num">
                                <CountUp value={total} format={format} />
                            </strong>
                            {centerLabel && <span>{centerLabel}</span>}
                        </>
                    )}
                </span>
            </div>
        </div>
    )
}
