import { isJulgadosUnit, type JulgadosUnit } from '../julgados-acordaos/fields.ts'
import type { DadoFaltando, JulgadosSentencasResponse, LinhaRelator, LinhaSentenca, PontoJulgados } from './types.ts'

// Mapa dos campos do Julgados Sentenças por unidade, e a leitura da resposta numa forma só (sem React; testado em
// fields.test.ts). Na v1 cada unidade tinha a sua página (NG/julgados_sentenca_NG.tsx, LA/julgados_sentenca_LA.tsx,
// RJ/julgados_sentenca_RJ.tsx), com os mesmos campos e o sufixo _NG, _LA ou _RJ (conferido nos modelos da API: as
// três unidades têm todos). Fonte dos nomes: DashboardStats e DashboardResponse em
// apps/api/src/app/analyses/v1_dashboard_julgados_sentenca.py.

export type { JulgadosUnit }

// Números de `stats` (nome-base; o sufixo da unidade entra em sentencasFields()).
const NUMEROS = {
    // Sentença (1º Grau), no período
    total: 'julgados_sentenca_total',
    procedentes: 'julgados_sentenca_procedentes',
    improcedentes: 'julgados_sentenca_improcedentes',
    extintos: 'julgados_sentenca_extintos',
    tempoMedio: 'julgados_sentenca_tempo_medio_dias', // ajuizamento -> sentença, em dias
    embargosTempoMedio: 'julgados_sentenca_embargos_tempo_medio_dias', // sentença -> sentença de embargos
    valorProcedentes: 'julgados_sentenca_valor_procedentes', // valor de causa das procedentes
    embargados: 'julgados_sentenca_embargados',
    revertidos: 'julgados_sentenca_revertidos',
    totalEstoque: 'julgados_sentenca_total_estoque', // toda a base já sentenciada
    // Estudos de Extinção: entrada = no período; estoque = toda a base já sentenciada
    extincaoValor: 'julgados_extincao_valor',
    extincaoTotalEstoque: 'julgados_extincao_total_estoque',
    extincaoValorEstoque: 'julgados_extincao_valor_estoque',
    extincaoRevertida: 'julgados_extincao_revertida_2g',
    extincaoRevertidaEstoque: 'julgados_extincao_revertida_2g_estoque',
    // Estudo das Improcedências
    improcedenciaValor: 'julgados_improcedencia_valor',
    improcedenciaTotalEstoque: 'julgados_improcedencia_total_estoque',
    improcedenciaValorEstoque: 'julgados_improcedencia_valor_estoque',
    improcedenciaRevertida: 'julgados_improcedencia_revertida_2g',
    improcedenciaRevertidaEstoque: 'julgados_improcedencia_revertida_2g_estoque',
    // Faixa "Atenção" (histórico todo, independente do período)
    semJuiz: 'julgados_sentenca_sem_juiz',
    semMateria: 'julgados_sentenca_sem_materia',
    semComarca: 'julgados_sentenca_sem_comarca',
    semCompetencia: 'julgados_sentenca_sem_competencia',
    semUf: 'julgados_sentenca_sem_uf',
    semValorPe: 'julgados_sentenca_sem_valor_pe',
    meritoSemData: 'julgados_sentenca_merito_sem_data',
    dataSemMerito: 'julgados_sentenca_data_sem_merito',
} as const

export type SentencasNumero = keyof typeof NUMEROS

// Os números que têm comparativo com o período anterior de mesma duração (comparativo_<nome-base>_<unidade>).
export const COMPARAVEIS = [
    'total',
    'procedentes',
    'improcedentes',
    'extintos',
    'tempoMedio',
    'valorProcedentes',
    'embargados',
    'revertidos',
] as const satisfies readonly SentencasNumero[]

export type SentencasComparavel = (typeof COMPARAVEIS)[number]

// Listas: as de `stats` (opções e faixa "Atenção") e as da raiz (gráficos e a lista).
const LISTAS = {
    ufOpcoes: 'stats.julgados_uf_opcoes', // UFs da base inteira (sem filtro)
    comarcaOpcoes: 'stats.julgados_comarca_opcoes', // comarcas da base inteira (sem filtro)
    dadosFaltando: 'stats.julgados_sentenca_dados_faltando',
    ranking: 'ranking_juizes_sentenca_julgados',
    porMateria: 'julgados_por_materia',
    historicoPorMateria: 'historico_julgados_por_materia', // V2: a mesma lista, do histórico todo
    porCompetencia: 'julgados_por_competencia',
    porComarca: 'julgados_por_comarca',
    porMotivoExtincao: 'julgados_por_motivo_extincao', // extintas no período (o "entrada" dos Estudos de Extinção)
    porAnoAjuizamento: 'julgados_por_ano_ajuizamento',
    embargosResultado: 'julgados_sentenca_embargos_resultado',
    procedentesPorMes: 'julgados_sentenca_procedentes_por_mes', // histórico todo ('nov 2026')
    improcedentesPorMes: 'julgados_sentenca_improcedentes_por_mes',
    extintosPorMes: 'julgados_sentenca_extintos_por_mes',
    lista: 'julgados_sentenca_lista',
    extincaoPorComarca: 'julgados_extincao_por_comarca',
    extincaoPorComarcaEstoque: 'julgados_extincao_por_comarca_estoque',
    extincaoPorMotivoEstoque: 'julgados_extincao_por_motivo_estoque',
    extincaoPorJuiz: 'julgados_extincao_por_juiz',
    extincaoPorJuizEstoque: 'julgados_extincao_por_juiz_estoque',
    improcedenciaPorComarca: 'julgados_improcedencia_por_comarca',
    improcedenciaPorComarcaEstoque: 'julgados_improcedencia_por_comarca_estoque',
    improcedenciaPorMotivo: 'julgados_improcedencia_por_motivo',
    improcedenciaPorMotivoEstoque: 'julgados_improcedencia_por_motivo_estoque',
    improcedenciaPorJuiz: 'julgados_improcedencia_por_juiz',
    improcedenciaPorJuizEstoque: 'julgados_improcedencia_por_juiz_estoque',
} as const

export type SentencasLista = keyof typeof LISTAS

export const SENTENCAS_NUMEROS = Object.keys(NUMEROS) as SentencasNumero[]
export const SENTENCAS_LISTAS = Object.keys(LISTAS) as SentencasLista[]

// A unidade da resposta: pelo nome da rota da v1 ('julgados_LA'); sem ele, pelo código da unidade.
export function unidadeSentencas(data: Pick<JulgadosSentencasResponse, 'dashboard' | 'meta'>): JulgadosUnit | null {
    const rota = /^julgados_(NG|LA|RJ)$/.exec(data.dashboard ?? '')
    if (rota) return rota[1] as JulgadosUnit
    return isJulgadosUnit(data.meta.unit) ? data.meta.unit : null
}

export type SentencasFields = {
    numeros: Record<SentencasNumero, string | null>
    comparativos: Record<SentencasComparavel, string | null>
    listas: Record<SentencasLista, string | null> // 'stats.x' = dentro de stats
}

// Os nomes dos campos na unidade; null = unidade desconhecida.
export function sentencasFields(unit: JulgadosUnit | null): SentencasFields {
    const nome = (base: string) => (unit ? `${base}_${unit}` : null)
    const numeros = {} as Record<SentencasNumero, string | null>
    for (const k of SENTENCAS_NUMEROS) numeros[k] = nome(NUMEROS[k])
    const comparativos = {} as Record<SentencasComparavel, string | null>
    for (const k of COMPARAVEIS) comparativos[k] = nome(`comparativo_${NUMEROS[k]}`)
    const listas = {} as Record<SentencasLista, string | null>
    for (const k of SENTENCAS_LISTAS) listas[k] = nome(LISTAS[k])
    return { numeros, comparativos, listas }
}

// ---------- leitura (o que vier faltando ou com tipo errado vira null / lista vazia) ----------

const numero = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)
const texto = (v: unknown): string => (v === null || v === undefined ? '' : String(v))
const objetos = (v: unknown): Record<string, unknown>[] =>
    Array.isArray(v) ? v.filter((x): x is Record<string, unknown> => typeof x === 'object' && x !== null) : []

function pontos(v: unknown): PontoJulgados[] {
    return objetos(v)
        .map((p) => ({
            name: texto(p.name).trim(),
            value: numero(p.value) ?? 0,
            valorCausa: numero(p.valor_causa),
            uf: p.uf ? texto(p.uf).trim().toUpperCase() : null,
            tempoMedioDias: numero(p.tempo_medio_dias),
        }))
        .filter((p) => p.name !== '')
}

const textos = (v: unknown): string[] => (Array.isArray(v) ? v.map(texto).filter((s) => s.trim() !== '') : [])

function juizes(v: unknown): LinhaRelator[] {
    return objetos(v)
        .filter((r) => texto(r.name).trim() !== '')
        .map((r) => ({
            name: texto(r.name).trim(),
            initials: texto(r.initials),
            total: numero(r.total_casos) ?? 0,
            taxa: numero(r.taxa_sucesso) ?? 0,
            procedentes: numero(r.fav) ?? 0,
            improcedentes: numero(r.des) ?? 0,
            extintos: numero(r.outros) ?? 0,
            pctProcedentes: numero(r.percent_fav) ?? 0,
            pctImprocedentes: numero(r.percent_des) ?? 0,
            pctExtintos: numero(r.percent_outros) ?? 0,
        }))
}

const dia = (v: unknown): string | null => (typeof v === 'string' && v.trim() ? v.trim().slice(0, 10) : null)

function linhas(v: unknown): LinhaSentenca[] {
    return objetos(v).map((r) => ({
        id: numero(r.id),
        numero_processo: texto(r.numero_processo),
        fase: texto(r.fase),
        subfase: texto(r.subfase),
        status_1g: texto(r.status_1g),
        uf: texto(r.uf),
        juiz: texto(r.juiz),
        data_sentenca: dia(r.data_sentenca),
        status_sentenca_embargos: texto(r.status_sentenca_embargos),
        data_sentenca_embargos: dia(r.data_sentenca_embargos),
    }))
}

function faltando(v: unknown): DadoFaltando[] {
    return objetos(v)
        .map((r) => ({ numero_processo: texto(r.numero_processo), campo: texto(r.campo) }))
        .filter((r) => r.campo !== '')
}

export type Escopo = 'entrada' | 'estoque'

// Um estudo (Extinção ou Improcedência) num escopo: por comarca, por motivo e por juiz.
export type Estudo = { porComarca: PontoJulgados[]; porMotivo: PontoJulgados[]; porJuiz: PontoJulgados[] }

export type JulgadosSentencas = {
    unit: JulgadosUnit | null
    n: Record<SentencasNumero, number | null>
    comparativo: Record<SentencasComparavel, number | null>
    ufOpcoes: string[]
    comarcaOpcoes: string[]
    dadosFaltando: DadoFaltando[]
    ranking: LinhaRelator[]
    porMateria: PontoJulgados[]
    historicoPorMateria: PontoJulgados[]
    porCompetencia: PontoJulgados[]
    porComarca: PontoJulgados[]
    porMotivoExtincao: PontoJulgados[]
    porAnoAjuizamento: PontoJulgados[]
    embargosResultado: PontoJulgados[]
    porMes: { procedentes: PontoJulgados[]; improcedentes: PontoJulgados[]; extintos: PontoJulgados[] }
    lista: LinhaSentenca[]
    extincao: Record<Escopo, Estudo>
    improcedencia: Record<Escopo, Estudo>
}

// A resposta numa forma só, com os nomes da unidade certa.
export function lerJulgadosSentencas(resp: JulgadosSentencasResponse): JulgadosSentencas {
    const unit = unidadeSentencas(resp)
    const f = sentencasFields(unit)
    const stats = resp.stats ?? {}
    const bruto = (campo: string | null): unknown => {
        if (!campo) return undefined
        return campo.startsWith('stats.') ? stats[campo.slice(6)] : resp[campo]
    }
    const deStats = (campo: string | null) => (campo ? stats[campo] : undefined)
    const n = {} as Record<SentencasNumero, number | null>
    for (const k of SENTENCAS_NUMEROS) n[k] = numero(deStats(f.numeros[k]))
    const comparativo = {} as Record<SentencasComparavel, number | null>
    for (const k of COMPARAVEIS) comparativo[k] = numero(deStats(f.comparativos[k]))
    const lista = (k: SentencasLista) => pontos(bruto(f.listas[k]))

    return {
        unit,
        n,
        comparativo,
        ufOpcoes: textos(bruto(f.listas.ufOpcoes)).map((u) => u.trim().toUpperCase()),
        comarcaOpcoes: textos(bruto(f.listas.comarcaOpcoes)),
        dadosFaltando: faltando(bruto(f.listas.dadosFaltando)),
        ranking: juizes(bruto(f.listas.ranking)),
        porMateria: lista('porMateria'),
        historicoPorMateria: lista('historicoPorMateria'),
        porCompetencia: lista('porCompetencia'),
        porComarca: lista('porComarca'),
        porMotivoExtincao: lista('porMotivoExtincao'),
        porAnoAjuizamento: lista('porAnoAjuizamento'),
        embargosResultado: lista('embargosResultado'),
        porMes: {
            procedentes: lista('procedentesPorMes'),
            improcedentes: lista('improcedentesPorMes'),
            extintos: lista('extintosPorMes'),
        },
        lista: linhas(bruto(f.listas.lista)),
        // Na v1 o motivo das extinções "entrada" é o mesmo gráfico do período (julgados_por_motivo_extincao).
        extincao: {
            entrada: {
                porComarca: lista('extincaoPorComarca'),
                porMotivo: lista('porMotivoExtincao'),
                porJuiz: lista('extincaoPorJuiz'),
            },
            estoque: {
                porComarca: lista('extincaoPorComarcaEstoque'),
                porMotivo: lista('extincaoPorMotivoEstoque'),
                porJuiz: lista('extincaoPorJuizEstoque'),
            },
        },
        improcedencia: {
            entrada: {
                porComarca: lista('improcedenciaPorComarca'),
                porMotivo: lista('improcedenciaPorMotivo'),
                porJuiz: lista('improcedenciaPorJuiz'),
            },
            estoque: {
                porComarca: lista('improcedenciaPorComarcaEstoque'),
                porMotivo: lista('improcedenciaPorMotivoEstoque'),
                porJuiz: lista('improcedenciaPorJuizEstoque'),
            },
        },
    }
}
