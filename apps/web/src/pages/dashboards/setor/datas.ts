import { parseMonth } from '../../../lib/charts.ts'

// Datas e meses nos rótulos dos dashboards de setor (sem React; testado em datas.test.ts).

export const MESES = [
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
const MES_CURTO = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

// Uma cor por ano no "mês a mês"; o ano mais recente fica sempre com a cor principal.
export const CORES_ANO = ['var(--chart-1)', 'var(--chart-3)', 'var(--chart-4)', 'var(--chart-5)']

// 'abril' -> 'Abril' (caixa do cursor).
export const mesNome = (i: number) => MESES[i][0].toUpperCase() + MESES[i].slice(1)

// '2026-11-03' -> '03/11' (o ano já está no Período).
export function diaCurto(iso: string): string {
    const m = /^\d{4}-(\d{2})-(\d{2})$/.exec(iso)
    return m ? `${m[2]}/${m[1]}` : iso
}

// '2026-11-03' -> '03/11/2026'.
export function diaLongo(iso: string | undefined): string {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso ?? '')
    return m ? `${m[3]}/${m[2]}/${m[1]}` : (iso ?? '')
}

// '2026-11-04' a '2026-11-13' -> '04/11 a 13/11/2026' (ano repetido só quando muda).
export function periodo(from: string, to: string): string {
    if (!from || !to) return 'Período selecionado'
    const a = diaLongo(from)
    const b = diaLongo(to)
    return from.slice(0, 4) === to.slice(0, 4) ? `${a.slice(0, 5)} a ${b}` : `${a} a ${b}`
}

// 'nov 2026' -> 'Nov / 2026' (rótulo da barra do mês).
export function mesBarra(name: string): string {
    const m = parseMonth(name)
    return m ? `${MES_CURTO[m.month - 1]} / ${m.year}` : name
}
