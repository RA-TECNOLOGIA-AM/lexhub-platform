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
