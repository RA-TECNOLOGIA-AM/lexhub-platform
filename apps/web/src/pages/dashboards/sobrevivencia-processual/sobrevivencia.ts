import type { Meta } from '../../../types/index.ts'
import {
    ajustarKM,
    amostrarGrade,
    medianaKM,
    testeLogRank,
    type Observacao,
    type ResultadoLogRank,
} from './kaplanMeier.ts'

// Sobrevivência Processual (TCC): a página da v1 GERAL/TccSobrevivenciaProcessual.tsx. A API entrega a coorte do estudo
// (um processo por linha, em colunas + dicionários; app/dashboards/sobrevivencia_processual.py) e todo o cálculo
// (Kaplan-Meier, medianas, log-rank) roda aqui, no navegador, a cada filtro — como na v1.
// Só lógica pura (testada em sobrevivencia.test.ts).

type Col = (number | null)[]
export type SobrevivenciaResponse = {
    meta: Meta
    gerado_em?: string
    escritorio_dict?: string[]
    tipo_acao_dict?: string[]
    materia_dict?: string[]
    comarca_dict?: string[]
    competencia_dict?: string[]
    fase_dict?: string[]
    subfase_dict?: string[]
    juiz_1g_dict?: string[]
    relator_2g_dict?: string[]
    tipo_evento_e1_dict?: string[]
    tipo_evento_e2_dict?: string[]
    tipo_acordo_dict?: string[]
    registros?: Record<string, Col | undefined>
}

export type Linha = {
    escritorio: string | null
    duracaoE1: number
    eventoE1: 0 | 1
    tipoEvento1: string | null
    tipoAcordo: string | null
    duracaoAcordo: number | null
    tipoAcao: string | null
    materia: string | null
    comarca: string | null
    competencia: string | null
    fase: string | null
    subfase: string | null
    juiz1g: string | null
    relator2g: string | null
    tipoEvento2: string | null
    duracaoE2: number | null
    eventoSentenca: number
    sentencaFavoravel: number
    sentencaImprocedente: number
    sentencaExtinta: number
    duracaoSentenca: number | null
    eventoAcordao: number
    acordaoFavoravel: number
    acordaoImprocedente: number
    acordaoExtinto: number
    duracaoAcordao: number | null
}

// --- constantes da v1 ---
export const DIAS_GRADE = Array.from({ length: 31 }, (_, i) => i * 60) // 0, 60, …, 1800
export const TOP_CATEGORIAS_CURVA = 6
export const MIN_N = 30 // mínimo de processos por categoria (curvas, rankings e log-rank)
export const TOP_N_RANKING = 8
export const AMOSTRA_PEQUENA = 200
// Agravos e mandado de segurança não são "tipo de ação" do estudo (somem do ranking/filtro de tipo de ação).
const TIPO_ACAO_EXCLUIDO = /AGRAVO|MANDADO DE SEGURANÇA/i

// Decodifica o formato colunar uma vez (v1: decodificarLinhas).
export function decodificar(p: SobrevivenciaResponse): Linha[] {
    const r = p.registros ?? {}
    const col = (k: string): Col => r[k] ?? []
    const dic = (d: string[] | undefined, v: number | null | undefined) =>
        v === null || v === undefined ? null : (d?.[v] ?? null)
    const n = col('duracao_e1').length
    const linhas: Linha[] = []
    for (let i = 0; i < n; i++) {
        const tipoAcao = dic(p.tipo_acao_dict, col('tipo_acao')[i])
        linhas.push({
            escritorio: dic(p.escritorio_dict, col('escritorio')[i]),
            duracaoE1: col('duracao_e1')[i] ?? 0,
            eventoE1: col('evento_e1')[i] === 1 ? 1 : 0,
            tipoEvento1: dic(p.tipo_evento_e1_dict, col('tipo_evento_e1')[i]),
            tipoAcordo: dic(p.tipo_acordo_dict, col('tipo_acordo')[i]),
            duracaoAcordo: col('duracao_acordo')[i] ?? null,
            tipoAcao: tipoAcao && TIPO_ACAO_EXCLUIDO.test(tipoAcao) ? null : tipoAcao,
            materia: dic(p.materia_dict, col('materia')[i]),
            comarca: dic(p.comarca_dict, col('comarca')[i]),
            competencia: dic(p.competencia_dict, col('competencia')[i]),
            fase: dic(p.fase_dict, col('fase')[i]),
            subfase: dic(p.subfase_dict, col('subfase')[i]),
            juiz1g: dic(p.juiz_1g_dict, col('juiz_1g')[i]),
            relator2g: dic(p.relator_2g_dict, col('relator_2g')[i]),
            tipoEvento2: dic(p.tipo_evento_e2_dict, col('tipo_evento_e2')[i]),
            duracaoE2: col('duracao_e2')[i] ?? null,
            eventoSentenca: col('evento_sentenca')[i] ?? 0,
            sentencaFavoravel: col('sentenca_favoravel')[i] ?? 0,
            sentencaImprocedente: col('sentenca_improcedente')[i] ?? 0,
            sentencaExtinta: col('sentenca_extinta')[i] ?? 0,
            duracaoSentenca: col('duracao_sentenca')[i] ?? null,
            eventoAcordao: col('evento_acordao')[i] ?? 0,
            acordaoFavoravel: col('acordao_favoravel')[i] ?? 0,
            acordaoImprocedente: col('acordao_improcedente')[i] ?? 0,
            acordaoExtinto: col('acordao_extinto')[i] ?? 0,
            duracaoAcordao: col('duracao_acordao')[i] ?? null,
        })
    }
    return linhas
}

// --- filtros (clique nos gráficos; OU dentro de um campo, E entre campos) ---
export const CAMPOS = [
    'tipoAcao',
    'materia',
    'comarca',
    'competencia',
    'fase',
    'subfase',
    'juiz1g',
    'relator2g',
] as const
export type Campo = (typeof CAMPOS)[number]
export type Selecao = Record<Campo, string[]>
export const SELECAO_VAZIA: Selecao = Object.fromEntries(CAMPOS.map((c) => [c, []])) as unknown as Selecao
export const ROTULO_CAMPO: Record<Campo, string> = {
    tipoAcao: 'Tipo de ação',
    materia: 'Matéria',
    comarca: 'Comarca',
    competencia: 'Competência',
    fase: 'Fase',
    subfase: 'Subfase',
    juiz1g: 'Juiz (1G)',
    relator2g: 'Relator (2G)',
}

// Os filtros da página; `excluir` = o campo do próprio gráfico (ele continua mostrando todas as categorias).
export function aplicarFiltros(linhas: Linha[], selecao: Selecao, excluir?: Campo): Linha[] {
    const ativos = CAMPOS.filter((c) => c !== excluir && selecao[c].length > 0)
    if (ativos.length === 0) return linhas
    return linhas.filter((l) => ativos.every((c) => l[c] !== null && selecao[c].includes(l[c] as string)))
}

export const alternar = (selecao: Selecao, campo: Campo, nome: string): Selecao => ({
    ...selecao,
    [campo]: selecao[campo].includes(nome) ? selecao[campo].filter((v) => v !== nome) : [...selecao[campo], nome],
})

// --- observações para o Kaplan-Meier ---
export const obsEstagio1 = (ls: Linha[]): Observacao[] => ls.map((l) => ({ duracao: l.duracaoE1, evento: l.eventoE1 }))
export const obsEstagio2 = (ls: Linha[]): Observacao[] =>
    ls
        .filter((l) => l.duracaoE2 !== null && l.tipoEvento2 !== null)
        .map((l) => ({ duracao: l.duracaoE2 as number, evento: l.tipoEvento2 === 'PAGO' ? 1 : 0 }))
export const obsSentenca = (ls: Linha[]): Observacao[] =>
    ls
        .filter((l) => l.duracaoSentenca !== null)
        .map((l) => ({ duracao: l.duracaoSentenca as number, evento: l.eventoSentenca === 1 ? 1 : 0 }))
export const obsAcordao = (ls: Linha[]): Observacao[] =>
    ls
        .filter((l) => l.duracaoAcordao !== null)
        .map((l) => ({ duracao: l.duracaoAcordao as number, evento: l.eventoAcordao === 1 ? 1 : 0 }))

// A curva na grade de 0 a 1800 dias, em % (1 casa), como a v1.
export const curvaPct = (obs: Observacao[]) =>
    amostrarGrade(ajustarKM(obs), DIAS_GRADE).map((s) => Math.round(s * 1000) / 10)
export const mediana = (obs: Observacao[]) => (obs.length ? medianaKM(ajustarKM(obs)) : null)

// --- agrupamentos, rankings e log-rank ---
export function agruparPorVolume(ls: Linha[], campo: Campo, minN = MIN_N, topN = TOP_N_RANKING) {
    const grupos = new Map<string, Linha[]>()
    for (const l of ls) {
        const v = l[campo]
        if (!v) continue
        const g = grupos.get(v) ?? []
        g.push(l)
        grupos.set(v, g)
    }
    return [...grupos]
        .filter(([, g]) => g.length >= minN)
        .sort((a, b) => b[1].length - a[1].length)
        .slice(0, topN)
        .map(([nome, linhas]) => ({ nome, linhas }))
}

export type ItemRanking = { name: string; value: number; n: number }
export type Ranking = { itens: ItemRanking[]; logRank: ResultadoLogRank | null }

// Mediana KM por grupo (mais lento primeiro) e o log-rank entre os mesmos grupos (v1: calcularRanking + LogRankBadge).
export function ranking(grupos: { nome: string; linhas: Linha[] }[], obs: (ls: Linha[]) => Observacao[]): Ranking {
    const itens: ItemRanking[] = []
    for (const g of grupos) {
        const o = obs(g.linhas)
        const m = mediana(o)
        if (o.length === 0 || m === null) continue
        itens.push({ name: g.nome, value: m, n: o.length })
    }
    itens.sort((a, b) => b.value - a.value)
    return { itens, logRank: grupos.length >= 2 ? testeLogRank(grupos.map((g) => obs(g.linhas))) : null }
}

// Categorias das curvas comparativas: as 6 de maior volume com pelo menos 30 processos.
export function curvasPor(ls: Linha[], campo: Campo) {
    return agruparPorVolume(ls, campo, MIN_N, TOP_CATEGORIAS_CURVA).map((g) => ({
        nome: g.nome,
        n: g.linhas.length,
        valores: curvaPct(obsEstagio1(g.linhas)),
    }))
}

// --- KPIs do diagrama de fluxo (seção 01) ---
const pct = (num: number, den: number) => (den > 0 ? Math.round((1000 * num) / den) / 10 : null)
export function medianaSimples(v: number[]): number | null {
    if (v.length === 0) return null
    const o = [...v].sort((a, b) => a - b)
    const m = Math.floor(o.length / 2)
    return o.length % 2 ? o[m] : Math.round((o[m - 1] + o[m]) / 2)
}

export function resumo(ls: Linha[]) {
    const n = ls.length
    const conta = (f: (l: Linha) => boolean) => ls.filter(f).length
    const comSentenca = ls.filter((l) => l.eventoSentenca === 1)
    const comAcordao = ls.filter((l) => l.eventoAcordao === 1)
    const pre = ls.filter((l) => l.tipoAcordo === 'PRE_SENTENCA')
    const pos = ls.filter((l) => l.tipoAcordo === 'POS_SENTENCA')
    const comE2 = ls.filter((l) => l.tipoEvento2 !== null)
    const pagos = comE2.filter((l) => l.tipoEvento2 === 'PAGO').length
    return {
        coorte: n,
        medianaGeral: n ? mediana(obsEstagio1(ls)) : null,
        pctMeritoFavoravel: n
            ? pct(
                  conta((l) => l.tipoEvento1 === 'MERITO_FAVORAVEL_COM_PROVEITO'),
                  n,
              )
            : null,
        sentenca: {
            mediana: n ? mediana(obsSentenca(ls)) : null,
            favoravel: pct(comSentenca.filter((l) => l.sentencaFavoravel === 1).length, comSentenca.length),
            improcedente: pct(comSentenca.filter((l) => l.sentencaImprocedente === 1).length, comSentenca.length),
            extinta: pct(comSentenca.filter((l) => l.sentencaExtinta === 1).length, comSentenca.length),
        },
        acordao: {
            mediana: n ? mediana(obsAcordao(ls)) : null,
            favoravel: pct(comAcordao.filter((l) => l.acordaoFavoravel === 1).length, comAcordao.length),
            improcedente: pct(comAcordao.filter((l) => l.acordaoImprocedente === 1).length, comAcordao.length),
            extinta: pct(comAcordao.filter((l) => l.acordaoExtinto === 1).length, comAcordao.length),
        },
        // v1: a mediana do acordo é direta (sem censura), com a duração do acordo (ou a do E1, quando falta).
        acordoPre: {
            pct: n ? pct(pre.length, n) : null,
            mediana: medianaSimples(pre.map((l) => l.duracaoAcordo ?? l.duracaoE1)),
        },
        acordoPos: {
            pct: n ? pct(pos.length, n) : null,
            mediana: medianaSimples(pos.map((l) => l.duracaoAcordo ?? l.duracaoE1)),
        },
        estagio2: {
            elegiveis: comE2.length,
            pagos,
            taxa: comE2.length ? pct(pagos, comE2.length) : null,
            mediana: mediana(obsEstagio2(comE2)),
        },
    }
}

// p-valor como a v1: "p < 0,0001" ou "p = 0,0321".
export const formatarPValor = (p: number) => (p < 0.0001 ? 'p < 0,0001' : `p = ${p.toFixed(4).replace('.', ',')}`)
