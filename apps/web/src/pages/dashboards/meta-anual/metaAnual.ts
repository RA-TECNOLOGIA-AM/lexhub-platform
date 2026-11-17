import type { CardTrimestre, Trimestre, Zona, ZonaUI } from './types.ts'

// A lógica da página Meta anual (sem React; testada em metaAnual.test.ts), a mesma da página da v1
// (MetaAnualNG.tsx): zonas, régua e quanto falta para cada meta.

export const ZONAS: readonly Zona[] = ['TRISTE', 'BASE', 'AVANCADA', 'SUPER']

export const ZONA_NOME: Record<ZonaUI, string> = {
    ENTRADA: 'Entrada',
    TRISTE: 'Triste',
    BASE: 'Base',
    AVANCADA: 'Avançada',
    SUPER: 'Super',
}

// "No acumulado, estamos na zona base."
export const ZONA_FRASE: Record<ZonaUI, string> = {
    ENTRADA: 'zona de entrada',
    TRISTE: 'zona triste',
    BASE: 'zona base',
    AVANCADA: 'zona avançada',
    SUPER: 'super meta',
}

// Classe da cor de cada zona (app.css: .z-entrada, .z-triste...).
export const zonaClasse = (z: ZonaUI) => `z-${z.toLowerCase()}`

export type Metas = Record<Zona, number>

// A zona de um valor: a maior meta atingida (abaixo da Triste = Entrada).
export function zonaDe(valor: number, metas: Metas): ZonaUI {
    let z: ZonaUI = 'ENTRADA'
    for (const nivel of ZONAS) if (metas[nivel] > 0 && valor >= metas[nivel]) z = nivel
    return z
}

// A próxima zona e quanto falta para ela (Super atingida: nenhuma).
export function proximaZona(valor: number, metas: Metas): { zona: Zona | null; falta: number } {
    const proxima = ZONAS.find((z) => valor < metas[z]) ?? null
    return { zona: proxima, falta: proxima ? Math.max(0, metas[proxima] - valor) : 0 }
}

export const metasDoCard = (c: CardTrimestre): Metas => ({
    TRISTE: c.meta_triste,
    BASE: c.meta_base,
    AVANCADA: c.meta_avancada,
    SUPER: c.meta_super,
})

// A régua da v1: Entrada (0 → Triste), Triste, Base e Avançada proporcionais às metas (sobre a Super) e a
// faixa Super com largura fixa (8% a mais). Larguras e marcador em % da barra inteira.
export const SUPER_VISUAL = 8

// inicio = onde a faixa começa (% da barra), para a meta ficar embaixo do começo dela.
export type Regua = { faixas: { zona: ZonaUI; largura: number; inicio: number }[]; marcador: number }

export function regua(valor: number, metas: Metas): Regua {
    const { TRISTE: t, BASE: b, AVANCADA: a, SUPER: s } = metas
    if (s <= 0) return { faixas: [], marcador: 0 }
    const w = [t / s, (b - t) / s, (a - b) / s, (s - a) / s].map((x) => Math.max(0, x) * 100)
    const pista = w[0] + w[1] + w[2] + w[3]
    const total = pista + SUPER_VISUAL
    const dentro = (v: number, de: number, ate: number) =>
        ate > de ? Math.min(1, Math.max(0, (v - de) / (ate - de))) : 0
    let pos: number
    if (valor < t) pos = (t > 0 ? Math.min(1, Math.max(0, valor / t)) : 0) * w[0]
    else if (valor < b) pos = w[0] + dentro(valor, t, b) * w[1]
    else if (valor < a) pos = w[0] + w[1] + dentro(valor, b, a) * w[2]
    else if (valor < s) pos = w[0] + w[1] + w[2] + dentro(valor, a, s) * w[3]
    else pos = pista
    const zonas: ZonaUI[] = ['ENTRADA', 'TRISTE', 'BASE', 'AVANCADA', 'SUPER']
    return {
        faixas: zonas.map((zona, i) => ({
            zona,
            largura: ((i < 4 ? w[i] : SUPER_VISUAL) / total) * 100,
            inicio: (w.slice(0, i).reduce((acc, x) => acc + x, 0) / total) * 100,
        })),
        marcador: Math.min(100, Math.max(0, (pos / total) * 100)),
    }
}

// "Atingido e % que falta por meta": cada meta com o % atingido (até 100) e o que falta.
export function atingimentoPorMeta(valor: number, metas: Metas) {
    return ZONAS.map((zona) => {
        const meta = metas[zona]
        const pct = meta > 0 ? Math.min(100, (valor / meta) * 100) : 0
        return { zona, meta, pct, falta: 100 - pct }
    })
}

// '4T' -> '4º trimestre'
export const trimestreNome = (t: Trimestre) => `${t[0]}º trimestre`

const MESES = [
    'Janeiro',
    'Fevereiro',
    'Março',
    'Abril',
    'Maio',
    'Junho',
    'Julho',
    'Agosto',
    'Setembro',
    'Outubro',
    'Novembro',
    'Dezembro',
]
export const mesNome = (m: string | number) => MESES[Number(m) - 1] ?? String(m)

// Valor curto como na v1: 'R$ 4,91 mi', 'R$ 888,7 mil', 'R$ 950,00'.
const mi = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const mil = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 })
export function compacto(v: number): string {
    const abs = Math.abs(v)
    if (abs >= 1_000_000) return `R$ ${mi.format(v / 1_000_000)} mi`
    if (abs >= 1000) return `R$ ${mil.format(v / 1000)} mil`
    return `R$ ${mi.format(v)}`
}
