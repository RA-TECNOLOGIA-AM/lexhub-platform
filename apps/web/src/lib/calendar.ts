// Módulo: as contas do calendário, sem React (testado em calendar.test.ts).
// Datas no formato 'AAAA-MM-DD', como em lib/period.ts. Mês sempre de 0 a 11 (como o Date).

export const MONTH_NAMES = [
    'janeiro',
    'fevereiro',
    'março',
    'abril',
    'maio',
    'junho',
    'julho',
    'agosto',
    'setembro',
    'outubro',
    'novembro',
    'dezembro',
]
export const MONTH_SHORT = [
    'jan.',
    'fev.',
    'mar.',
    'abr.',
    'mai.',
    'jun.',
    'jul.',
    'ago.',
    'set.',
    'out.',
    'nov.',
    'dez.',
]
// Semana começa no domingo (padrão do Brasil).
export const WEEKDAYS = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S']

const pad = (n: number) => String(n).padStart(2, '0')

export const isoOf = (y: number, m: number, d: number): string => {
    const date = new Date(y, m, d) // normaliza estouro (dia 0, mês 12...)
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export const partsOf = (iso: string) => {
    const [y, m, d] = iso.split('-').map(Number)
    return { y, m: m - 1, d }
}

// '2026-11-26' -> '26/11/2026' (vazio fica vazio).
export const formatBr = (iso: string): string => {
    if (!iso) return ''
    const { y, m, d } = partsOf(iso)
    return `${pad(d)}/${pad(m + 1)}/${y}`
}

// Soma dias a uma data (aceita negativo).
export const addDays = (iso: string, days: number): string => {
    const { y, m, d } = partsOf(iso)
    return isoOf(y, m, d + days)
}

// Mesma data em outro mês; o dia é cortado no último dia do mês (31/jan + 1 = 28/fev).
export const addMonths = (iso: string, months: number): string => {
    const { y, m, d } = partsOf(iso)
    const last = new Date(y, m + months + 1, 0).getDate()
    return isoOf(y, m + months, Math.min(d, last))
}

// As 6 semanas do mês (42 dias, começando no domingo), com os dias de fora marcados.
export function monthGrid(y: number, m: number): { iso: string; day: number; inMonth: boolean }[] {
    const start = 1 - new Date(y, m, 1).getDay()
    return Array.from({ length: 42 }, (_, i) => {
        const date = new Date(y, m, start + i)
        return {
            iso: isoOf(date.getFullYear(), date.getMonth(), date.getDate()),
            day: date.getDate(),
            inMonth: date.getMonth() === ((m % 12) + 12) % 12,
        }
    })
}

// Onde o dia cai no intervalo De→Até (para pintar a faixa).
export function rangeRole(iso: string, from: string, to: string): 'start' | 'end' | 'single' | 'inside' | null {
    if (!from || !to || from > to) return iso === from || iso === to ? 'single' : null
    if (iso === from && iso === to) return 'single'
    if (iso === from) return 'start'
    if (iso === to) return 'end'
    if (iso > from && iso < to) return 'inside'
    return null
}
