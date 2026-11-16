// Módulo: as contas dos gráficos, sem React (testado em charts.test.ts).

export type XY = { x: number; y: number }

// Eixo "redondo" a partir do maior valor: 151 -> 0, 40, 80, 120, 160 (como os gráficos da v1).
export function niceScale(max: number, count = 4): { max: number; ticks: number[] } {
    if (!(max > 0)) return { max: 1, ticks: [0, 1] }
    const raw = max / count
    const mag = 10 ** Math.floor(Math.log10(raw))
    const step = [1, 1.5, 2, 2.5, 4, 5, 8, 10].map((n) => n * mag).find((s) => s >= raw) ?? 10 * mag
    const top = Math.ceil(max / step) * step
    const ticks: number[] = []
    for (let v = 0; v <= top + step / 2; v += step) ticks.push(Number(v.toFixed(10)))
    return { max: top, ticks }
}

// Curva suave que não passa do ponto (monotone cubic, Fritsch-Carlson): a linha nunca inventa um pico
// que não existe nos dados. Devolve o atributo `d` de um <path>.
export function smoothPath(points: XY[]): string {
    const n = points.length
    if (n === 0) return ''
    if (n === 1) return `M${points[0].x},${points[0].y}`
    if (n === 2) return `M${points[0].x},${points[0].y}L${points[1].x},${points[1].y}`

    const dx: number[] = []
    const slope: number[] = []
    for (let i = 0; i < n - 1; i++) {
        dx.push(points[i + 1].x - points[i].x)
        slope.push((points[i + 1].y - points[i].y) / (dx[i] || 1))
    }
    const tangent: number[] = [slope[0]]
    for (let i = 1; i < n - 1; i++) {
        tangent.push(slope[i - 1] * slope[i] <= 0 ? 0 : (slope[i - 1] + slope[i]) / 2)
    }
    tangent.push(slope[n - 2])
    for (let i = 0; i < n - 1; i++) {
        if (slope[i] === 0) {
            tangent[i] = 0
            tangent[i + 1] = 0
            continue
        }
        const a = tangent[i] / slope[i]
        const b = tangent[i + 1] / slope[i]
        const h = a * a + b * b
        if (h > 9) {
            const t = 3 / Math.sqrt(h)
            tangent[i] = t * a * slope[i]
            tangent[i + 1] = t * b * slope[i]
        }
    }

    const r = (v: number) => Math.round(v * 100) / 100
    let d = `M${r(points[0].x)},${r(points[0].y)}`
    for (let i = 0; i < n - 1; i++) {
        const p = points[i]
        const q = points[i + 1]
        const h = dx[i] / 3
        d += `C${r(p.x + h)},${r(p.y + tangent[i] * h)} ${r(q.x - h)},${r(q.y - tangent[i + 1] * h)} ${r(q.x)},${r(q.y)}`
    }
    return d
}

const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

// Mês de um ponto mensal. A API manda 'nov 2026' (igual à v1); o mock, '2026-11'. Outro formato = null.
export function parseMonth(name: string): { year: number; month: number } | null {
    const iso = /^(\d{4})-(\d{2})$/.exec(name.trim())
    if (iso) return { year: Number(iso[1]), month: Number(iso[2]) }
    const br = /^([a-zç]{3})\w*\.?\s+(\d{4})$/i.exec(name.trim())
    if (br) {
        const month = MESES.indexOf(br[1].toLowerCase()) + 1
        return month > 0 ? { year: Number(br[2]), month } : null
    }
    return null
}

// 'nov 2026' -> 'nov/2026' (rótulo curto do eixo).
export function monthLabel(name: string): string {
    const m = parseMonth(name)
    return m ? `${MESES[m.month - 1]}/${m.year}` : name
}

// Pontos mensais em ordem cronológica (a v1 ordena pelo texto, o que põe 'abr' antes de 'jan').
export function sortByMonth<T extends { name: string }>(points: T[]): T[] {
    const key = (p: T) => {
        const m = parseMonth(p.name)
        return m ? m.year * 12 + m.month : Number.POSITIVE_INFINITY
    }
    return [...points].sort((a, b) => key(a) - key(b))
}

// Uma linha por ano, janeiro a dezembro (null = mês sem dado): o "Protocolados mês a mês" da v1.
export function seriesByYear(points: { name: string; value: number }[]): { year: number; values: (number | null)[] }[] {
    const years = new Map<number, (number | null)[]>()
    for (const p of points) {
        const m = parseMonth(p.name)
        if (!m) continue
        const values = years.get(m.year) ?? Array<number | null>(12).fill(null)
        values[m.month - 1] = (values[m.month - 1] ?? 0) + p.value
        years.set(m.year, values)
    }
    return [...years.entries()].sort(([a], [b]) => a - b).map(([year, values]) => ({ year, values }))
}

// Os N maiores, do maior para o menor (empate: ordem que veio).
export function topN<T extends { value: number }>(points: T[], n = 10): T[] {
    return points
        .map((p, i) => ({ p, i }))
        .sort((a, b) => b.p.value - a.p.value || a.i - b.i)
        .slice(0, n)
        .map(({ p }) => p)
}

// Rótulos empilhados ao lado de uma coluna (partes finas): cada um no meio da sua parte, empurrado para cima
// quando encosta no de baixo. Recebe os y de baixo para cima (y cresce para baixo); devolve o y de cada um.
export function spreadLabels(ys: number[], gap = 13): number[] {
    const out: number[] = []
    for (const y of ys) out.push(out.length ? Math.min(y, out[out.length - 1] - gap) : y)
    return out
}

export type PieSlice = { name: string; value: number; share: number; start: number; end: number; others: number }

// Fatias da pizza: as `max` maiores, em ordem, e o resto somado numa fatia "Outras" (others = quantas juntou).
// start/end em frações da volta (0–1), share em %. sort = false mantém a ordem recebida (ex.: Resolvidos antes
// de Não resolvidos).
export function pieSlices(
    items: { name: string; value: number }[],
    max = 10,
    othersLabel = 'Outras',
    sort = true,
): PieSlice[] {
    const positive = items.filter((p) => p.value > 0)
    const sorted = sort ? topN(positive, positive.length) : positive
    const total = sorted.reduce((sum, p) => sum + p.value, 0)
    if (total === 0) return []
    const head = sorted.length > max + 1 ? sorted.slice(0, max) : sorted
    const rest = sorted.slice(head.length)
    const parts = rest.length
        ? [...head, { name: othersLabel, value: rest.reduce((sum, p) => sum + p.value, 0), others: rest.length }]
        : head
    let acc = 0
    return parts.map((p) => {
        const start = acc / total
        acc += p.value
        return {
            name: p.name,
            value: p.value,
            share: (p.value / total) * 100,
            start,
            end: acc / total,
            others: 'others' in p ? (p.others as number) : 0,
        }
    })
}

// Caminho SVG de uma fatia (de start a end, frações da volta, começando no topo e no sentido horário).
// inner > 0: fatia de rosca (anel entre inner e r).
export function arcPath(cx: number, cy: number, r: number, start: number, end: number, inner = 0): string {
    const pt = (rad: number, f: number) => {
        const a = f * 2 * Math.PI - Math.PI / 2
        return `${(cx + rad * Math.cos(a)).toFixed(2)},${(cy + rad * Math.sin(a)).toFixed(2)}`
    }
    if (end - start >= 0.9999) {
        // Volta inteira: duas meias-voltas (um arco só de 360° não desenha).
        const outer = `M${pt(r, 0)}A${r},${r} 0 1 1 ${pt(r, 0.5)}A${r},${r} 0 1 1 ${pt(r, 0)}Z`
        return inner > 0
            ? `${outer}M${pt(inner, 0)}A${inner},${inner} 0 1 0 ${pt(inner, 0.5)}A${inner},${inner} 0 1 0 ${pt(inner, 0)}Z`
            : outer
    }
    const large = end - start > 0.5 ? 1 : 0
    if (inner <= 0) return `M${cx},${cy}L${pt(r, start)}A${r},${r} 0 ${large} 1 ${pt(r, end)}Z`
    return `M${pt(r, start)}A${r},${r} 0 ${large} 1 ${pt(r, end)}L${pt(inner, end)}A${inner},${inner} 0 ${large} 0 ${pt(inner, start)}Z`
}

// Rótulos de uma coluna de texto (um lado da pizza): mantém cada um o mais perto possível do y desejado, sem
// ficarem a menos de `gap` um do outro e dentro de [min, max]. Devolve os y na mesma ordem da entrada.
export function spreadColumn(ys: number[], gap: number, min: number, max: number): number[] {
    const order = ys.map((y, i) => ({ y, i })).sort((a, b) => a.y - b.y || a.i - b.i)
    const pos = order.map((o) => o.y)
    for (let k = 0; k < pos.length; k++) pos[k] = Math.max(pos[k], k ? pos[k - 1] + gap : min)
    for (let k = pos.length - 1; k >= 0; k--) {
        pos[k] = Math.min(pos[k], k < pos.length - 1 ? pos[k + 1] - gap : max)
    }
    const out = new Array<number>(ys.length)
    order.forEach((o, k) => (out[o.i] = pos[k]))
    return out
}
