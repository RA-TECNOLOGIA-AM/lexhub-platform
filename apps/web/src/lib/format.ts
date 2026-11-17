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
const nf2 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const nfAte2 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 })
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
    dec2: (v: number) => nf2.format(v), // 3,94 (razões da v1: aproveitamento, TRE, ROAS)
    fator: (v: number) => `${nfAte2.format(v)}×`, // 4× (fator multiplicador da comissão)
    brl: (v: number) => brl.format(v), // R$ 14.355,72
    brlShort: (v: number) => brlCompact.format(v), // R$ 18,4 mi
    pct: (v: number) => nf1.format(v) + '%', // 8,2%
    dias: (v: number) => nf1.format(v) + (Math.abs(v - 1) < 0.05 ? ' dia' : ' dias'), // 2,4 dias
    pct2: (v: number) => nf2.format(v) + '%', // 46,53% (comparativo "vs mês anterior" da v1)
    duracao, // 0,34 dia -> 8h 10min (tempos no setor, como na v1)
    eixo, // valores do eixo dos gráficos: 1.284 · 500 mil · 1,2 mi (curto, para não cortar)
}

// Valor no eixo vertical dos gráficos: inteiro até 9.999; acima, em mil ou mi (o eixo tem pouco espaço).
const nfEixo = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 })
function eixo(v: number): string {
    const abs = Math.abs(v)
    if (abs >= 1_000_000) return `${nfEixo.format(v / 1_000_000)} mi`
    if (abs >= 10_000) return `${nfEixo.format(v / 1000)} mil`
    return nf0.format(v)
}

// Tempo em dias (como a API manda) no formato da v1: '58min', '8h 10min', '2d 3h'.
export function duracao(dias: number): string {
    const totalMin = Math.max(0, Math.round(dias * 24 * 60))
    if (totalMin < 60) return `${totalMin}min`
    const h = Math.floor(totalMin / 60)
    const min = totalMin % 60
    if (h < 24) return min ? `${h}h ${min}min` : `${h}h`
    const d = Math.floor(h / 24)
    const hr = h % 24
    return hr ? `${d}d ${hr}h` : `${d}d`
}

// Valor que pode faltar na resposta (campo null ou ausente, ex.: mock sem números): '—'.
// Uso: show(s.total, fmt.int)
export function show(v: number | null | undefined, format: (v: number) => string): string {
    return v === null || v === undefined || Number.isNaN(v) ? '—' : format(v)
}
