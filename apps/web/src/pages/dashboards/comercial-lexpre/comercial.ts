import type { LinhaAtendente } from './types.ts'

// Contas da tela do Comercial (LexPre), sem React (testadas em comercial.test.ts).

// Metas da v1 (Meta por Atendente): R$ 12 mi por trimestre e R$ 24 mi por semestre, cada atendente.
export const META_TRIMESTRE = 12_000_000
export const META_SEMESTRE = 24_000_000
// Meta anual da empresa (card "Meta <ano>" do topo da v1): valor de causa protocolado no ano.
export const META_ANUAL = 270_000_000

export type PeriodoMeta = 'T1' | 'T2' | 'T3' | 'T4' | 'S1' | 'S2'

export const PERIODOS_META: { value: PeriodoMeta; label: string }[] = [
    { value: 'T1', label: '1º Trimestre (Jan–Mar)' },
    { value: 'T2', label: '2º Trimestre (Abr–Jun)' },
    { value: 'T3', label: '3º Trimestre (Jul–Set)' },
    { value: 'T4', label: '4º Trimestre (Out–Dez)' },
    { value: 'S1', label: '1º Semestre (Jan–Jun)' },
    { value: 'S2', label: '2º Semestre (Jul–Dez)' },
]

const MESES: Record<PeriodoMeta, [number, number]> = {
    T1: [1, 3],
    T2: [4, 6],
    T3: [7, 9],
    T4: [10, 12],
    S1: [1, 6],
    S2: [7, 12],
}

const pad = (n: number) => String(n).padStart(2, '0')

// O trimestre em que uma data cai (padrão do seletor, como na v1): '2026-11-13' -> 'T4'.
export function trimestreDe(iso: string): PeriodoMeta {
    const mes = Number(iso.slice(5, 7)) || 1
    return (['T1', 'T2', 'T3', 'T4'] as const)[Math.floor((mes - 1) / 3)]
}

// Datas do período no ano: ('T4', 2026) -> { from: '2026-10-01', to: '2026-12-31' }.
export function datasDoPeriodo(periodo: PeriodoMeta, ano: number): { from: string; to: string } {
    const [ini, fim] = MESES[periodo]
    const ultimoDia = new Date(ano, fim, 0).getDate()
    return { from: `${ano}-${pad(ini)}-01`, to: `${ano}-${pad(fim)}-${pad(ultimoDia)}` }
}

export const metaDoPeriodo = (periodo: PeriodoMeta) => (periodo.startsWith('S') ? META_SEMESTRE : META_TRIMESTRE)

export type LinhaMeta = { name: string; protocolado: number; meta: number; faltam: number; pct: number }

// Meta por Atendente da v1: cada atendente contra a meta do período, do que mais protocolou ao que menos.
export function linhasMeta(protocoladoPorAtendente: Record<string, number>, meta: number, limite = 10): LinhaMeta[] {
    return Object.entries(protocoladoPorAtendente)
        .map(([name, valor]) => {
            const protocolado = Number(valor) || 0
            return {
                name,
                protocolado,
                meta,
                faltam: Math.max(0, meta - protocolado),
                pct: meta > 0 ? Math.max(0, (protocolado / meta) * 100) : 0,
            }
        })
        .sort((a, b) => b.protocolado - a.protocolado)
        .slice(0, limite)
}

// Faixa de cor do atingimento (as mesmas da v1): >= 96 verde, >= 81 laranja, >= 51 amarelo, abaixo vermelho.
export function faixaAtingimento(pct: number): 'ok' | 'accent' | 'warn' | 'danger' {
    if (pct >= 96) return 'ok'
    if (pct >= 81) return 'accent'
    if (pct >= 51) return 'warn'
    return 'danger'
}

// Colunas do "Detalhamento por Atendente", na ordem da API: geral primeiro e depois cada canal
// (leads_<canal> · clientes_<canal> · taxa_<canal>). 'retorno_ativo' -> 'Retorno Ativo'.
export function canaisDaTabela(linhas: LinhaAtendente[]): { slug: string; label: string }[] {
    const vistos: string[] = []
    for (const l of linhas) {
        for (const k of Object.keys(l)) {
            const m = /^leads_(.+)$/.exec(k)
            if (m && !vistos.includes(m[1])) vistos.push(m[1])
        }
    }
    const ordenados = ['geral', ...vistos.filter((s) => s !== 'geral')]
    return ordenados.filter((s) => vistos.includes(s)).map((slug) => ({ slug, label: rotuloCanal(slug) }))
}

export function rotuloCanal(slug: string): string {
    return slug
        .split('_')
        .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
        .join(' ')
}

// Média de uma coluna entre os atendentes (a cor da v1: acima da média = verde, abaixo = vermelho).
export function mediaDaColuna(linhas: LinhaAtendente[], coluna: string): number {
    const valores = linhas.map((l) => Number(l[coluna]) || 0)
    return valores.length ? valores.reduce((a, b) => a + b, 0) / valores.length : 0
}

// Progresso da meta anual: % atingido (0–100, como a v1) e quanto falta (nunca negativo).
export function progressoMeta(valor: number, meta: number): { pct: number; faltam: number } {
    const v = Number.isFinite(valor) ? Math.max(0, valor) : 0
    const pct = meta > 0 ? Math.min(100, (v / meta) * 100) : 0
    return { pct, faltam: Math.max(0, meta - v) }
}

// Chave de um nome para juntar os bancos: sem caixa, acento e espaços sobrando ('MARIA ' = 'Maria' = 'María').
const chaveNome = (nome: string) =>
    nome
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .trim()
        .toLowerCase()

// 'JOBSON' -> 'Jobson' (nome que só veio do legado, que guarda tudo em maiúsculas no LA).
const capitalizar = (nome: string) =>
    nome
        .trim()
        .toLowerCase()
        .replace(/(^|\s)\S/g, (c) => c.toUpperCase())

// Soma dois "nome -> valor" (LexPre + legado na Meta por Atendente, como a v1: pelo primeiro nome), juntando o
// mesmo nome escrito diferente nos dois bancos ('Maria' + 'MARIA'). Fica a grafia do primeiro (o LexPre).
export function somarPorNome(a: Record<string, number>, b: Record<string, number> = {}): Record<string, number> {
    const nomes = new Map<string, string>()
    const out: Record<string, number> = {}
    for (const [nome, v] of [...Object.entries(a), ...Object.entries(b)]) {
        const chave = chaveNome(nome)
        if (!nomes.has(chave)) nomes.set(chave, nome === nome.toUpperCase() ? capitalizar(nome) : nome.trim())
        const exibido = nomes.get(chave)!
        out[exibido] = (out[exibido] ?? 0) + (Number(v) || 0)
    }
    return out
}
