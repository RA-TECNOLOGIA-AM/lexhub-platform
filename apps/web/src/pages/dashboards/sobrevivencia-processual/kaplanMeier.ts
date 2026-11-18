/**
 * Estimador de Kaplan-Meier (product-limit) em TypeScript, pra rodar no navegador
 * sobre o dado linha a linha da pagina de Sobrevivencia Processual (TCC).
 *
 * Equivalente ao `lifelines.KaplanMeierFitter` usado antes no pipeline Python —
 * ver TCC - Luiz/scripts/atualizar_dashboard_tcc.py (versao anterior) pra conferencia.
 */

export interface Observacao {
    duracao: number
    evento: 0 | 1 // 1 = evento observado, 0 = censurado
}

export interface CurvaSobrevivencia {
    /** Tempos unicos (dias) onde a sobrevivencia muda, em ordem crescente. Sempre comeca implicitamente em 0 -> 1.0. */
    tempos: number[]
    /** S(t) apos cada tempo em `tempos`, mesma ordem/indice. */
    sobrevivencia: number[]
    n: number
}

const CURVA_VAZIA: CurvaSobrevivencia = { tempos: [], sobrevivencia: [], n: 0 }

/** Ajusta a curva de Kaplan-Meier. O(n log n). */
export function ajustarKM(obs: Observacao[]): CurvaSobrevivencia {
    if (obs.length === 0) return CURVA_VAZIA

    const ordenado = [...obs].sort((a, b) => a.duracao - b.duracao)
    const n = ordenado.length

    const tempos: number[] = []
    const sobrevivencia: number[] = []

    let sAtual = 1
    let emRisco = n
    let i = 0
    while (i < n) {
        const t = ordenado[i].duracao
        let eventos = 0
        let total = 0
        while (i < n && ordenado[i].duracao === t) {
            total += 1
            if (ordenado[i].evento === 1) eventos += 1
            i += 1
        }
        if (eventos > 0) {
            sAtual *= 1 - eventos / emRisco
            tempos.push(t)
            sobrevivencia.push(sAtual)
        }
        emRisco -= total
    }

    return { tempos, sobrevivencia, n }
}

/** S(dia): ultimo valor de sobrevivencia conhecido ate `dia` (funcao em escada). 1.0 antes do primeiro evento. */
export function sobrevivenciaEm(curva: CurvaSobrevivencia, dia: number): number {
    if (curva.tempos.length === 0) return 1
    let lo = 0
    let hi = curva.tempos.length - 1
    if (dia < curva.tempos[0]) return 1
    if (dia >= curva.tempos[hi]) return curva.sobrevivencia[hi]
    while (lo < hi) {
        const mid = Math.ceil((lo + hi) / 2)
        if (curva.tempos[mid] <= dia) lo = mid
        else hi = mid - 1
    }
    return curva.sobrevivencia[lo]
}

/** Reamostra a curva numa grade fixa de dias (pra plotar). */
export function amostrarGrade(curva: CurvaSobrevivencia, grade: number[]): number[] {
    return grade.map((d) => sobrevivenciaEm(curva, d))
}

/** Mediana: primeiro dia em que S(t) <= 0.5. `null` se a curva nunca chega la (censura pesada / amostra pequena). */
export function medianaKM(curva: CurvaSobrevivencia): number | null {
    for (let idx = 0; idx < curva.tempos.length; idx++) {
        if (curva.sobrevivencia[idx] <= 0.5) return curva.tempos[idx]
    }
    return null
}

/** Atalho: ajusta a curva e ja devolve so a mediana (usado nos rankings, onde a curva em si nao e exibida). */
export function medianaDireta(obs: Observacao[]): number | null {
    return medianaKM(ajustarKM(obs))
}

/* ──────────────────────────────────────────────────────────────────────────
 * Teste de log-rank multivariado (Mantel-Haenszel / Peto), o mesmo algoritmo
 * de `lifelines.statistics.multivariate_logrank_test` (Python) e do
 * `survdiff()` do R. Usado pra responder: "a diferenca entre as curvas de
 * sobrevivencia dos grupos e estatisticamente significativa, ou pode ser
 * so coincidencia da amostra?"
 * ──────────────────────────────────────────────────────────────────────── */

export interface ResultadoLogRank {
    chi2: number
    df: number
    pValor: number
    /** Eventos observados vs. esperados sob a hipotese nula (sem diferenca entre grupos), por grupo. */
    observadoPorGrupo: number[]
    esperadoPorGrupo: number[]
}

/** Resolve A*x = b por eliminacao de Gauss-Jordan com pivotamento parcial. `null` se o sistema for singular. */
function resolverSistemaLinear(a: number[][], b: number[]): number[] | null {
    const n = b.length
    if (n === 0) return []
    const m = a.map((linha, i) => [...linha, b[i]])

    for (let col = 0; col < n; col++) {
        let linhaPivo = col
        for (let r = col + 1; r < n; r++) {
            if (Math.abs(m[r][col]) > Math.abs(m[linhaPivo][col])) linhaPivo = r
        }
        if (Math.abs(m[linhaPivo][col]) < 1e-12) return null
        ;[m[col], m[linhaPivo]] = [m[linhaPivo], m[col]]
        for (let r = 0; r < n; r++) {
            if (r === col) continue
            const fator = m[r][col] / m[col][col]
            if (fator === 0) continue
            for (let c = col; c <= n; c++) m[r][c] -= fator * m[col][c]
        }
    }
    return m.map((linha, i) => linha[n] / linha[i])
}

/** log(Gamma(x)) via aproximacao de Lanczos. */
function logGamma(x: number): number {
    const g = 7
    const c = [
        0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059,
        12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7,
    ]
    if (x < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * x)) - logGamma(1 - x)
    const xx = x - 1
    let a = c[0]
    const t = xx + g + 0.5
    for (let i = 1; i < g + 2; i++) a += c[i] / (xx + i)
    return 0.5 * Math.log(2 * Math.PI) + (xx + 0.5) * Math.log(t) - t + Math.log(a)
}

/** Funcao gama incompleta regularizada inferior P(s, x) — base da CDF da qui-quadrado. */
function gamaIncompletaRegularizada(s: number, x: number): number {
    if (x <= 0 || s <= 0) return 0
    if (x < s + 1) {
        // serie de potencias
        let soma = 1 / s
        let termo = soma
        let n = s
        for (let i = 0; i < 500; i++) {
            n += 1
            termo *= x / n
            soma += termo
            if (Math.abs(termo) < Math.abs(soma) * 1e-15) break
        }
        return soma * Math.exp(-x + s * Math.log(x) - logGamma(s))
    }
    // fracao continua de Lentz, pra cauda superior (depois inverte: P = 1 - Q)
    const FPMIN = 1e-300
    let b = x + 1 - s
    let c = 1 / FPMIN
    let d = 1 / b
    let h = d
    for (let i = 1; i < 500; i++) {
        const an = -i * (i - s)
        b += 2
        d = an * d + b
        if (Math.abs(d) < FPMIN) d = FPMIN
        c = b + an / c
        if (Math.abs(c) < FPMIN) c = FPMIN
        d = 1 / d
        const delta = d * c
        h *= delta
        if (Math.abs(delta - 1) < 1e-15) break
    }
    const q = Math.exp(-x + s * Math.log(x) - logGamma(s)) * h
    return 1 - q
}

/** CDF da distribuicao qui-quadrado com `k` graus de liberdade. */
function cdfQuiQuadrado(x: number, k: number): number {
    return gamaIncompletaRegularizada(k / 2, x / 2)
}

/**
 * Teste de log-rank multivariado entre 2+ grupos. `grupos[i]` e a lista de
 * observacoes (duracao + evento) do grupo i, na mesma ordem dos `labels`
 * (labels sao so pra facilitar o chamador, nao influenciam o calculo).
 *
 * Retorna `null` se houver menos de 2 grupos com dado, ou se a matriz de
 * variancia for singular (acontece quando os grupos nao se sobrepoem no
 * tempo o suficiente pra comparar).
 */
export function testeLogRank(grupos: Observacao[][]): ResultadoLogRank | null {
    const k = grupos.length
    if (k < 2) return null
    if (grupos.some((g) => g.length === 0)) return null

    const todos: { duracao: number; evento: 0 | 1; grupo: number }[] = []
    grupos.forEach((g, idx) => g.forEach((o) => todos.push({ ...o, grupo: idx })))
    todos.sort((a, b) => a.duracao - b.duracao)

    const nTotalRegistros = todos.length
    const emRisco = grupos.map((g) => g.length)
    const observado = new Array(k).fill(0)
    const esperado = new Array(k).fill(0)
    const variancia: number[][] = Array.from({ length: k }, () => new Array(k).fill(0))

    let i = 0
    while (i < nTotalRegistros) {
        const t = todos[i].duracao
        const dPorGrupo = new Array(k).fill(0)
        let dTotal = 0
        let j = i
        while (j < nTotalRegistros && todos[j].duracao === t) {
            if (todos[j].evento === 1) {
                dPorGrupo[todos[j].grupo] += 1
                dTotal += 1
            }
            j += 1
        }

        const nTotal = emRisco.reduce((s, v) => s + v, 0)

        if (dTotal > 0 && nTotal > 0) {
            for (let g = 0; g < k; g++) {
                observado[g] += dPorGrupo[g]
                esperado[g] += dTotal * (emRisco[g] / nTotal)
            }
            if (nTotal > 1) {
                const fator = (dTotal * (nTotal - dTotal)) / (nTotal - 1)
                for (let g = 0; g < k; g++) {
                    const ng = emRisco[g] / nTotal
                    for (let h = 0; h < k; h++) {
                        const nh = emRisco[h] / nTotal
                        variancia[g][h] += fator * ng * ((g === h ? 1 : 0) - nh)
                    }
                }
            }
        }

        // remove do risco todo mundo com essa duracao (evento ou censura)
        for (let m = i; m < j; m++) emRisco[todos[m].grupo] -= 1
        i = j
    }

    // so k-1 graus de liberdade (a soma de observado-esperado em todos os grupos e sempre 0,
    // entao a matriz completa k x k e singular — descarta o ultimo grupo como referencia).
    const dim = k - 1
    const diffCompleto = observado.map((o, idx) => o - esperado[idx])
    const diff = diffCompleto.slice(0, dim)
    const vSub = variancia.slice(0, dim).map((linha) => linha.slice(0, dim))

    const x = resolverSistemaLinear(vSub, diff)
    if (!x) return null

    let chi2 = 0
    for (let m = 0; m < dim; m++) chi2 += diff[m] * x[m]
    if (!Number.isFinite(chi2) || chi2 < 0) return null

    const pValor = 1 - cdfQuiQuadrado(chi2, dim)

    return { chi2, df: dim, pValor, observadoPorGrupo: observado, esperadoPorGrupo: esperado }
}
