import type { Meta, Point } from '../types.ts'

// Peças comuns a todos os mocks de dashboard.

const now = Date.now()

// Data ISO de "m minutos atrás" (para synced_at).
export const minAgo = (m: number) => new Date(now - m * 60_000).toISOString()

// Série diária determinística (dias úteis de outubro/2026), sem Math.random.
function porDia(base: number, amp: number, dias: number): Point[] {
    const out: Point[] = []
    for (let d = 1; d <= dias; d++) {
        const wd = new Date(2026, 9, d).getDay()
        if (wd === 0 || wd === 6) continue
        const v = Math.round(base + amp * Math.sin(d * 1.7) + (d % 5) * 2)
        out.push({ name: String(d).padStart(2, '0') + '/10', value: Math.max(0, v) })
    }
    return out
}

export const funcionarios = ['Carla Souza', 'Bruno Melo', 'Diego Rocha', 'Fernanda Lopes', 'Gabriel Torres', 'Helena Dias']

// Bloco `meta` de uma resposta: de onde e de quando são os dados da unidade.
export function metaFor(unit: string, source = 'LexPre'): Meta {
    return { unit, from: '2026-10-01', to: '2026-10-31', source, synced_at: minAgo(4) }
}

// "Tamanho" de cada unidade no mock (NG = base). Unidade nova = uma linha aqui.
const UNIT_SIZE: Record<string, number> = { NG: 1, LA_AM: 0.62, LA_RJ: 0.38 }

// Módulo: escala números-base para uma unidade.
// Contagens, valores e séries crescem com o tamanho; tempos, taxas e médias por pessoa, não
// (uma unidade menor não é mais rápida só por ser menor), então esses ficam fora daqui.
export function unitScale(unit: string) {
    const k = UNIT_SIZE[unit] ?? 1
    return {
        count: (v: number) => Math.round(v * k), // quantidade
        money: (v: number) => v * k, // valor em R$
        series: (base: number, amp: number) => porDia(base * k, amp * k, 31), // série por dia útil
        named: (items: [string, number][]): Point[] =>
            items.map(([name, value]) => ({ name, value: Math.round(value * k) })), // lista nome + quantidade
    }
}