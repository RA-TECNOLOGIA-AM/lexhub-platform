// Módulo: o período dos dashboards, sem React (testado em period.test.ts).
// Datas sempre no formato 'AAAA-MM-DD' (o mesmo da API). Strings nesse formato comparam certo com < e >.

export type Period = { from: string; to: string }

export type PresetKey = 'este-mes' | 'mes-passado' | 'ultimos-30' | 'este-ano'

// Atalhos: só preenchem De e Até; a pessoa ainda pode ajustar.
export const PRESETS: { key: PresetKey; label: string }[] = [
    { key: 'este-mes', label: 'Este mês' },
    { key: 'mes-passado', label: 'Mês passado' },
    { key: 'ultimos-30', label: 'Últimos 30 dias' },
    { key: 'este-ano', label: 'Este ano' },
]

const pad = (n: number) => String(n).padStart(2, '0')

// Data local -> 'AAAA-MM-DD'. (toISOString usaria UTC e, à noite, mostraria o dia seguinte.)
const toIso = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

export const todayIso = (now: Date = new Date()): string => toIso(now)

// O período de um atalho, contado a partir de "hoje" (now).
export function presetPeriod(key: PresetKey, now: Date = new Date()): Period {
    const y = now.getFullYear()
    const m = now.getMonth()
    const today = toIso(now)
    switch (key) {
        case 'este-mes':
            return { from: toIso(new Date(y, m, 1)), to: today }
        case 'mes-passado':
            // Dia 0 do mês atual = último dia do mês anterior.
            return { from: toIso(new Date(y, m - 1, 1)), to: toIso(new Date(y, m, 0)) }
        case 'ultimos-30':
            return { from: toIso(new Date(y, m, now.getDate() - 29)), to: today }
        case 'este-ano':
            return { from: toIso(new Date(y, 0, 1)), to: today }
    }
}

// O que está errado no período escolhido (null = está certo). Período é livre: qualquer data até hoje.
export function periodError(p: Period, today: string = todayIso()): string | null {
    if (!p.from || !p.to) return 'Escolha as duas datas.'
    if (p.from > p.to) return 'A data inicial precisa ser antes da final.'
    if (p.to > today) return 'A data final não pode ser depois de hoje.'
    return null
}

// Meses fixos (o Intl muda de navegador para navegador e usa espaço invisível).
const MONTHS = ['jan.', 'fev.', 'mar.', 'abr.', 'mai.', 'jun.', 'jul.', 'ago.', 'set.', 'out.', 'nov.', 'dez.']

const parts = (iso: string) => {
    const [y, m, d] = iso.split('-').map(Number)
    return { y, month: MONTHS[m - 1], d }
}

// O texto do botão, sem repetir o que é igual nas duas pontas:
// '5 de out. de 2026' · '1 a 30 de out. de 2026' · '28 de set. a 5 de out. de 2026' · '1 de dez. de 2025 a 31 de jan. de 2026'
export function periodLabel({ from, to }: Period): string {
    const a = parts(from)
    const b = parts(to)
    if (from === to) return `${a.d} de ${a.month} de ${a.y}`
    if (a.y === b.y && a.month === b.month) return `${a.d} a ${b.d} de ${b.month} de ${b.y}`
    if (a.y === b.y) return `${a.d} de ${a.month} a ${b.d} de ${b.month} de ${b.y}`
    return `${a.d} de ${a.month} de ${a.y} a ${b.d} de ${b.month} de ${b.y}`
}
