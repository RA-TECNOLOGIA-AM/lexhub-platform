// Previsão Individualizada (TCC, Fase 6): o cálculo da página da v1 GERAL/TccPrevisaoIndividualizada.tsx, sem mudança.
// O bundle (rota da v1 /tcc_previsao_individual) traz o lookup do XGBoost-AFT por combinação; a mistura de log-normais,
// os quantis, a KM da matéria e os cenários do 1G rodam no navegador. Na V2 o bundle já vem só com o escritório da
// unidade (NG vê NG, LA vê LA), então não há mais o filtro de escritório.

import type { Meta } from '../../../types/index.ts'

export type Exibicao = 'previsao' | 'relativo' | 'historico'

export type PrevisaoResponse = {
    meta: Meta
    gerado_em?: string
    modelo?: string
    n_treino?: number
    fracao_extinto_1g_desfavoravel?: number
    opcoes: {
        tiposAcao: string[]
        materias: string[]
        comarcas: string[]
        competencias: string[]
        escritorios: string[]
        faixasValor: string[]
    }
    grupo_modelo?: Partial<Record<'materia' | 'comarca' | 'competencia', Record<string, string>>>
    // "tipo|matéria|comarca|competência|escritório|faixa" (categorias do modelo) -> [dias, p1G‰, p2G‰ ×3, acPós‰ ×3, acPré‱]
    previsoes: Record<string, number | number[]>
    // "matéria|comarca|competência|tipo|escritório|faixa" (categorias reais)
    pesos_treino: Record<string, number>
    procedencia?: Record<string, number[]> // [julgados 1G, favoráveis 1G, julgados 2G, favoráveis 2G]
    historico_acordo_pre?: Record<string, number[]> // [resolvidos no 1G, acordos pré-sentença]
    referencia_acordo_pre?: Record<string, { media_prevista_12m: number; taxa_observada_12m: number }>
    exibicao?: Partial<Record<'procedencia_1g' | 'procedencia_2g' | 'acordo_pre' | 'acordo_pos', Exibicao>>
    km_materia?: Record<string, number[][]> // [tempo, eventos, censuras]
    medianas_materia?: Record<string, number | null>
    metricas_procedencia?: Record<string, { auc_xgb?: number; auc_logistica?: number }>
    metricas_procedencia_2g?: { modelo?: string; auc_xgb?: number; auc_logistica?: number }
    metricas?: {
        cindex?: Record<string, { teste?: number; ic95_min?: number; ic95_max?: number }>
        vitorias_pareadas_bootstrap?: { xgb_vs_cox_pct?: number; xgb_vs_rsf_pct?: number; rsf_vs_cox_pct?: number }
        brier_score_integrado?: Record<string, number>
        calibracao_90_dias?: { modelo: string; quartil: number; n?: number; previsto: number; observado: number }[]
    }
}

export const RESULTADOS_1G = ['Procedente', 'Improcedente', 'Extinto sem mérito'] as const
export type Resultado1G = (typeof RESULTADOS_1G)[number]
export type Ponderacao = 'historico' | 'igual'

export type Selecao = {
    materias: string[]
    comarcas: string[]
    competencias: string[]
    tipos: string[]
    faixas: string[]
    resultados1g: Resultado1G[]
    ponderacao: Ponderacao
}

export const SELECAO_VAZIA: Selecao = {
    materias: [],
    comarcas: [],
    competencias: [],
    tipos: [],
    faixas: [],
    resultados1g: [],
    ponderacao: 'historico',
}

export const MODELOS = [
    { k: 'Cox', label: 'Cox' },
    { k: 'RSF_tunada', label: 'RSF tunada' },
    { k: 'XGBoost_AFT', label: 'XGBoost-AFT' },
] as const

export const MIN_N = 30 // abaixo disso: "amostra pequena" / "base pequena"

type Previsao = { dias: number; p1g?: number; p2g?: number[]; acPos?: number[]; acPre?: number }

// Os formatos do bundle (o atual tem 9 números; os antigos, só os dias ou menos posições).
export function lerPrevisao(v: number | number[] | undefined): Previsao | null {
    if (v === undefined || v === null) return null
    if (typeof v === 'number') return { dias: v }
    const p: Previsao = { dias: v[0] }
    if (v.length > 1) p.p1g = v[1] / 1000
    if (v.length > 4) p.p2g = [v[2] / 1000, v[3] / 1000, v[4] / 1000]
    if (v.length > 7) p.acPos = [v[5] / 1000, v[6] / 1000, v[7] / 1000]
    if (v.length > 8) p.acPre = v[8] / 10000
    return p
}

export type Componente = Previsao & { peso: number; n: number; esc: string }

// Os valores efetivos: vazio = todas as opções do bundle.
export function efetivos(data: PrevisaoResponse, s: Selecao) {
    const o = data.opcoes
    return {
        materias: new Set(s.materias.length ? s.materias : o.materias),
        comarcas: new Set(s.comarcas.length ? s.comarcas : o.comarcas),
        competencias: new Set(s.competencias.length ? s.competencias : o.competencias),
        tipos: new Set(s.tipos.length ? s.tipos : o.tiposAcao),
        escritorios: new Set(o.escritorios),
        faixas: new Set(s.faixas.length ? s.faixas : o.faixasValor),
        materiasLista: s.materias.length ? s.materias : o.materias,
    }
}

type Ef = ReturnType<typeof efetivos>

// "matéria|comarca|competência|tipo|escritório|faixa" dentro da seleção? (as chaves antigas de 3 partes ficam fora)
function casa(chave: string, ef: Ef): string[] | null {
    const p = chave.split('|')
    if (p.length < 6) return null
    const [m, c, k, t, e, fx] = p
    if (!ef.materias.has(m) || !ef.comarcas.has(c) || !ef.competencias.has(k)) return null
    if (!ef.tipos.has(t) || !ef.escritorios.has(e) || !ef.faixas.has(fx)) return null
    return p
}

// Cada combinação real com processos de treino vira um componente da mistura (a previsão é a do grupo do modelo:
// categoria fora do top usa a de "Outros", mas entra com o peso da categoria real).
export function componentes(data: PrevisaoResponse, s: Selecao): { comps: Componente[]; nTreino: number } {
    const ef = efetivos(data, s)
    const g = (campo: 'materia' | 'comarca' | 'competencia', v: string) => data.grupo_modelo?.[campo]?.[v] ?? v
    const brutos: (Previsao & { n: number; esc: string })[] = []
    let total = 0
    for (const [chave, n] of Object.entries(data.pesos_treino ?? {})) {
        const p = casa(chave, ef)
        if (!p) continue
        const [m, c, k, t, e, fx] = p
        const prev = lerPrevisao(
            data.previsoes[[t, g('materia', m), g('comarca', c), g('competencia', k), e, fx].join('|')],
        )
        if (!prev) continue
        brutos.push({ ...prev, n, esc: e })
        total += n
    }
    if (total === 0) return { comps: [], nTreino: 0 }
    const comps = brutos.map((b) => ({ ...b, peso: s.ponderacao === 'igual' ? 1 / brutos.length : b.n / total }))
    return { comps, nTreino: total }
}

// Φ(z) — Abramowitz-Stegun 7.1.26 (o mesmo da v1).
export function phi(z: number): number {
    const sign = z < 0 ? -1 : 1
    const x = Math.abs(z) / Math.SQRT2
    const t = 1 / (1 + 0.3275911 * x)
    const y =
        1 -
        ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) *
            t *
            Math.exp(-x * x)
    return 0.5 * (1 + sign * y)
}

// S(t) da AFT log-normal com σ = 1 centrada na mediana.
export const sLogNormal = (t: number, mediana: number) => (t <= 0 ? 1 : 1 - phi(Math.log(t / mediana)))

export const sMistura = (t: number, comps: Componente[]) =>
    comps.reduce((acc, c) => acc + c.peso * sLogNormal(t, c.dias), 0)

// O tempo em que S da mistura cai para `alvo` (bisseção em log t entre 1 e 100.000 dias).
export function quantil(comps: Componente[], alvo: number): number {
    let lo = 0
    let hi = Math.log(100000)
    for (let i = 0; i < 60; i++) {
        const mid = (lo + hi) / 2
        if (sMistura(Math.exp(mid), comps) > alvo) lo = mid
        else hi = mid
    }
    return Math.round(Math.exp((lo + hi) / 2))
}

// Mediana Kaplan-Meier da união das matérias (treino inteiro da matéria: não filtra o resto).
export function medianaKmMaterias(data: PrevisaoResponse, materias: string[]): number | null {
    if (!data.km_materia) return materias.length === 1 ? (data.medianas_materia?.[materias[0]] ?? null) : null
    const porT = new Map<number, [number, number]>()
    let emRisco = 0
    for (const m of materias) {
        for (const [t, d, c] of data.km_materia[m] ?? []) {
            const a = porT.get(t) ?? [0, 0]
            a[0] += d
            a[1] += c
            porT.set(t, a)
            emRisco += d + c
        }
    }
    let s = 1
    for (const t of [...porT.keys()].sort((a, b) => a - b)) {
        const [d, c] = porT.get(t)!
        if (d > 0) s *= 1 - d / emRisco
        if (s <= 0.5) return t
        emRisco -= d + c
    }
    return null
}

// A grade da curva: 22 pontos de 0 a `fim` (420 a 3.000 dias, 2,2× a maior mediana, arredondado a 100).
export function gradeCurva(m: number): number[] {
    const fim = Math.min(3000, Math.max(420, Math.ceil((m * 2.2) / 100) * 100))
    const passo = fim / 21
    return Array.from({ length: 22 }, (_, i) => Math.round(i * passo))
}

const soma = (comps: Componente[], f: (c: Componente) => number) => comps.reduce((a, c) => a + c.peso * f(c), 0)

export type Cenarios = { seProcedente: number; seImprocedente: number; seExtinto: number; combinada: number | null }

// 2G e acordo pós por cenário do 1G, e a combinação pelos pesos da procedência 1G prevista.
export function porCenario1G(
    comps: Componente[],
    campo: 'p2g' | 'acPos',
    p1g: number | null,
    f: number,
): Cenarios | null {
    if (comps.length === 0 || comps.some((c) => !c[campo])) return null
    const seProcedente = soma(comps, (c) => c[campo]![0])
    const seImprocedente = soma(comps, (c) => c[campo]![1])
    const seExtinto = soma(comps, (c) => c[campo]![2])
    const combinada = p1g !== null ? p1g * seProcedente + (1 - p1g) * (f * seExtinto + (1 - f) * seImprocedente) : null
    return { seProcedente, seImprocedente, seExtinto, combinada }
}

export function escolherCenario(
    c: Cenarios | null,
    resultados: Resultado1G[],
    p1g: number | null,
    f: number,
): number | null {
    if (!c) return null
    if (resultados.length === 0) return c.combinada
    const p1 = p1g ?? 0.5
    const pesos: Record<Resultado1G, [number, number]> = {
        Procedente: [p1, c.seProcedente],
        Improcedente: [(1 - p1) * (1 - f), c.seImprocedente],
        'Extinto sem mérito': [(1 - p1) * f, c.seExtinto],
    }
    let w = 0
    let v = 0
    for (const r of resultados) {
        w += pesos[r][0]
        v += pesos[r][0] * pesos[r][1]
    }
    return w === 0 ? null : v / w
}

// Soma de uma tabela histórica (procedência, acordo pré) nas combinações da seleção.
function somaHistorico(tabela: Record<string, number[]> | undefined, ef: Ef, tamanho: number): number[] {
    const out = Array<number>(tamanho).fill(0)
    for (const [chave, v] of Object.entries(tabela ?? {})) {
        if (!casa(chave, ef)) continue
        for (let i = 0; i < tamanho; i++) out[i] += v[i] ?? 0
    }
    return out
}

export type Calculo = ReturnType<typeof calcular>

// Tudo o que a página mostra para uma seleção.
export function calcular(data: PrevisaoResponse, s: Selecao) {
    const ef = efetivos(data, s)
    const { comps, nTreino } = componentes(data, s)
    const tem = comps.length > 0
    const f = data.fracao_extinto_1g_desfavoravel ?? 0.3
    const diasPrevisto = tem ? quantil(comps, 0.5) : null
    const faixa = tem ? { de: quantil(comps, 0.75), ate: quantil(comps, 0.25) } : null
    const p1g = !tem || comps.some((c) => c.p1g === undefined) ? null : soma(comps, (c) => c.p1g!)
    const c2g = porCenario1G(comps, 'p2g', p1g, f)
    const cPos = porCenario1G(comps, 'acPos', p1g, f)
    const valor2g = escolherCenario(c2g, s.resultados1g, p1g, f)
    const acordoPos = escolherCenario(cPos, s.resultados1g, p1g, f)

    // Acordo pré: o modo vem do bundle (escolhido na validação temporal).
    const modo = data.exibicao?.acordo_pre ?? 'relativo'
    const semPre = !tem || comps.some((c) => c.acPre === undefined)
    const absoluto = semPre ? null : soma(comps, (c) => c.acPre!)
    const refs = data.referencia_acordo_pre
    const aproximado =
        semPre || !refs || comps.some((c) => !refs[c.esc])
            ? null
            : soma(comps, (c) => (c.acPre! / refs[c.esc].media_prevista_12m) * refs[c.esc].taxa_observada_12m)
    const [resolvidos, acordos] = somaHistorico(data.historico_acordo_pre, ef, 2)
    const historicoPre = resolvidos > 0 ? { n: resolvidos, a: acordos, taxa: acordos / resolvidos } : null
    const acordoPre = modo === 'previsao' ? absoluto : modo !== 'historico' ? aproximado : (historicoPre?.taxa ?? null)

    const [j1, f1, j2, f2] = somaHistorico(data.procedencia, ef, 4)
    const medianaMateria = medianaKmMaterias(data, ef.materiasLista)
    const delta = diasPrevisto !== null && medianaMateria !== null ? diasPrevisto - medianaMateria : null

    return {
        nTreino,
        diasPrevisto,
        faixa,
        p1g,
        c2g,
        valor2g,
        acordoPos,
        acordoPre,
        historicoPre,
        historico: { j1, f1, j2, f2 },
        medianaMateria,
        delta,
        comps,
    }
}

// A curva "Este caso" (mistura) e a da matéria (log-normal na mediana KM), em % ainda em tramitação.
export function curva(c: Calculo): { dias: number[]; caso: number[]; materia: (number | null)[] } {
    const m = Math.max(c.diasPrevisto ?? 0, c.medianaMateria ?? 0)
    const dias = gradeCurva(m)
    const r1 = (v: number) => Math.round(v * 1000) / 10
    return {
        dias,
        caso: dias.map((d) => r1(sMistura(d, c.comps))),
        materia: dias.map((d) => (c.medianaMateria === null ? null : r1(sLogNormal(d, c.medianaMateria)))),
    }
}

// As opções que têm treino no escritório da unidade (as listas do formulário).
export function disponiveis(data: PrevisaoResponse) {
    const vistos = [new Set<string>(), new Set<string>(), new Set<string>()]
    for (const chave of Object.keys(data.pesos_treino ?? {})) {
        const p = chave.split('|')
        if (p.length > 4 && !data.opcoes.escritorios.includes(p[4])) continue
        for (let i = 0; i < 3; i++) vistos[i].add(p[i])
    }
    return {
        materias: data.opcoes.materias.filter((v) => vistos[0].has(v)),
        comarcas: data.opcoes.comarcas.filter((v) => vistos[1].has(v)),
        competencias: data.opcoes.competencias.filter((v) => vistos[2].has(v)),
    }
}

// Quantas categorias o modelo distingue (as do top; o resto vai para "Outros").
export function nModelo(data: PrevisaoResponse, campo: 'materia' | 'comarca' | 'competencia'): number {
    const lista = {
        materia: data.opcoes.materias,
        comarca: data.opcoes.comarcas,
        competencia: data.opcoes.competencias,
    }[campo]
    const grupo = data.grupo_modelo?.[campo] ?? {}
    return lista.filter((v) => !(v in grupo) && v !== 'Não informada' && v !== 'Outros').length
}

// Pílulas: alterna; com todas marcadas volta para "Todos" (vazio), como na v1.
export function alternarPilula<T extends string>(sel: T[], v: T, todas: readonly T[]): T[] {
    const next = sel.includes(v) ? sel.filter((x) => x !== v) : [...sel, v]
    return next.length === todas.length ? [] : next
}

// Leitura do bootstrap pareado.
export function lerVitoria(pct: number | undefined, rival: string): string {
    if (pct === undefined) return '—'
    if (pct >= 95) return `vantagem consistente sobre o ${rival}`
    if (pct <= 5) return `o ${rival} é consistentemente melhor`
    return `empate técnico com o ${rival}`
}

// Formatadores da v1.
const virgula = (s: string) => s.replace('.', ',')
export const pct = (v: number) => `${Math.round(v * 100)}%`
export const pct1 = (v: number) => {
    const p = v * 100
    return p < 10 ? `${virgula(p.toFixed(1))}%` : `${Math.round(p)}%`
}
export const pctJa = (v: number) => `${virgula(v.toFixed(1))}%` // v já em %
export const dec = (v: number, casas: number) => virgula(v.toFixed(casas))
export function taxaProcedencia(fav: number, julg: number): string {
    return julg ? `${Math.round((100 * fav) / julg)}%` : '—'
}
