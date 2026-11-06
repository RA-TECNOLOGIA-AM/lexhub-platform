// Formatação pt-BR usada nas telas (vem do template/app.js).

// Minutos desde uma data ISO (ex.: '2026-11-06T13:00:00Z').
export function minutesSince(iso: string, now: number = Date.now()): number {
    return (now - new Date(iso).getTime()) / 60_000
}

// 'agora', 'há 4 min', 'há 2 h', 'há 3 d'
export function timeAgo(iso: string, now: number = Date.now()): string {
    const min = Math.max(0, Math.round(minutesSince(iso, now)))
    if (min < 1) return 'agora'
    if (min < 60) return `há ${min} min`
    const h = Math.round(min / 60)
    return h < 24 ? `há ${h} h` : `há ${Math.round(h / 24)} d`
}

// Números no padrão brasileiro (1.284 · R$ 14.355,72 · 8,2%).
const nf0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 })
const nf1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const brlCompact = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    notation: 'compact',
    maximumFractionDigits: 1,
})

export const fmt = {
    int: (v: number) => nf0.format(v), // 1.284
    dec1: (v: number) => nf1.format(v), // 9,4
    brl: (v: number) => brl.format(v), // R$ 14.355,72
    brlShort: (v: number) => brlCompact.format(v), // R$ 18,4 mi
    pct: (v: number) => nf1.format(v) + '%', // 8,2%
    dias: (v: number) => nf1.format(v) + (Math.abs(v - 1) < 0.05 ? ' dia' : ' dias'), // 2,4 dias
}
