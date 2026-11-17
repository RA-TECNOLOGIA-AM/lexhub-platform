import type { DadoFaltando, JulgadosAcordaosResponse, LinhaAcordao, LinhaRelator, PontoJulgados } from './types.ts'

// Mapa dos campos do Julgados Acórdãos por unidade, e a leitura da resposta numa forma só (sem React; testado em
// fields.test.ts). Na v1 cada unidade tinha a sua página (NG/julgados_acordao_NG.tsx, LA/julgados_acordao_LA.tsx,
// RJ/julgados_acordao_RJ.tsx), com os mesmos campos e o sufixo _NG, _LA ou _RJ. Fonte dos nomes: DashboardStats e
// DashboardResponse em apps/api/src/app/analyses/v1_dashboard_julgados.py. O que não existe numa unidade fica null
// (a tela mostra '—'); hoje só os recursos ao STJ/STF do Estudo das Improcedências, que a LA e o RJ não têm.

export type JulgadosUnit = 'NG' | 'LA' | 'RJ'

// Números de `stats` (nome-base; o sufixo da unidade entra em julgadosFields()).
const NUMEROS = {
    // Acórdão (2º Grau), no período
    total: 'julgados_acordao_total',
    procedentes: 'julgados_acordao_procedentes',
    improcedentes: 'julgados_acordao_improcedentes',
    extintos: 'julgados_acordao_extintos',
    naoClassificados: 'julgados_acordao_nao_classificados',
    tempoMedio: 'julgados_acordao_tempo_medio_dias', // sentença -> acórdão, em dias
    embargosTempoMedio: 'julgados_acordao_embargos_tempo_medio_dias', // acórdão -> acórdão de embargos
    valorProcedentes: 'julgados_acordao_valor_procedentes', // valor de causa inicial dos procedentes
    valorFixado: 'julgados_acordao_valor_fixado_procedentes', // VALOR_ACORDAO dos procedentes (o card da v1)
    embargados: 'julgados_acordao_embargados', // embargos com data no período
    revertidos: 'julgados_acordao_revertidos', // embargos "Revertido Ganho"
    // Estudo das Improcedências: entrada = no período; estoque = toda a base já julgada
    improcedenciaValor: 'julgados_acordao_improcedencia_valor',
    improcedenciaTotalEstoque: 'julgados_acordao_improcedencia_total_estoque',
    improcedenciaValorEstoque: 'julgados_acordao_improcedencia_valor_estoque',
    improcedenciaStj: 'julgados_acordao_improcedencia_stj',
    improcedenciaStf: 'julgados_acordao_improcedencia_stf',
    improcedenciaStjEstoque: 'julgados_acordao_improcedencia_stj_estoque',
    improcedenciaStfEstoque: 'julgados_acordao_improcedencia_stf_estoque',
    totalEstoque: 'julgados_acordao_total_estoque',
    // Faixa "Atenção" (histórico todo, independente do período)
    semRelator: 'julgados_acordao_sem_relator',
    semMateria: 'julgados_acordao_sem_materia',
    semComarca: 'julgados_acordao_sem_comarca',
    semCompetencia: 'julgados_acordao_sem_competencia',
    semUf: 'julgados_acordao_sem_uf',
    semValorPe: 'julgados_acordao_sem_valor_pe',
    meritoSemData: 'julgados_acordao_merito_sem_data',
    dataSemMerito: 'julgados_acordao_data_sem_merito',
} as const

export type JulgadosNumero = keyof typeof NUMEROS

// Os números que têm comparativo com o período anterior de mesma duração (comparativo_<nome-base>_<unidade>).
export const COMPARAVEIS = [
    'total',
    'procedentes',
    'improcedentes',
    'extintos',
    'naoClassificados',
    'tempoMedio',
    'valorProcedentes',
    'valorFixado',
    'embargados',
    'revertidos',
] as const satisfies readonly JulgadosNumero[]

export type JulgadosComparavel = (typeof COMPARAVEIS)[number]

// Listas: as de `stats` (opções e faixa "Atenção") e as da raiz (gráficos e a lista).
const LISTAS = {
    ufOpcoes: 'stats.julgados_acordao_uf_opcoes', // UFs da base inteira (sem filtro)
    comarcaOpcoes: 'stats.julgados_comarca_opcoes', // comarcas da base inteira (sem filtro)
    dadosFaltando: 'stats.julgados_acordao_dados_faltando',
    ranking: 'ranking_relatores_acordao_julgados',
    porMateria: 'julgados_acordao_por_materia',
    historicoPorMateria: 'historico_julgados_acordao_por_materia', // V2: a mesma lista, do histórico todo
    porCompetencia: 'julgados_acordao_por_competencia',
    porComarca: 'julgados_acordao_por_comarca',
    porMotivoExtincao: 'julgados_acordao_por_motivo_extincao',
    porAnoAjuizamento: 'julgados_acordao_por_ano_ajuizamento',
    embargosResultado: 'julgados_acordao_embargos_resultado',
    procedentesPorMes: 'julgados_acordao_procedentes_por_mes', // histórico todo ('nov 2026')
    improcedentesPorMes: 'julgados_acordao_improcedentes_por_mes',
    extintosPorMes: 'julgados_acordao_extintos_por_mes',
    lista: 'julgados_acordao_lista',
    improcedenciaPorComarca: 'julgados_acordao_improcedencia_por_comarca',
    improcedenciaPorComarcaEstoque: 'julgados_acordao_improcedencia_por_comarca_estoque',
    improcedenciaPorMotivo: 'julgados_acordao_improcedencia_por_motivo',
    improcedenciaPorMotivoEstoque: 'julgados_acordao_improcedencia_por_motivo_estoque',
    improcedenciaPorRelator: 'julgados_acordao_improcedencia_por_relator',
    improcedenciaPorRelatorEstoque: 'julgados_acordao_improcedencia_por_relator_estoque',
} as const

export type JulgadosLista = keyof typeof LISTAS

// Campos que não existem numa unidade (conferido nos modelos da API: só a NG conta os recursos ao STJ/STF).
const FALTA: Record<JulgadosUnit, readonly string[]> = {
    NG: [],
    LA: ['improcedenciaStj', 'improcedenciaStf', 'improcedenciaStjEstoque', 'improcedenciaStfEstoque'],
    RJ: ['improcedenciaStj', 'improcedenciaStf', 'improcedenciaStjEstoque', 'improcedenciaStfEstoque'],
}

export const JULGADOS_NUMEROS = Object.keys(NUMEROS) as JulgadosNumero[]
export const JULGADOS_LISTAS = Object.keys(LISTAS) as JulgadosLista[]

export function isJulgadosUnit(unit: string): unit is JulgadosUnit {
    return unit === 'NG' || unit === 'LA' || unit === 'RJ'
}

// A unidade da resposta: pelo nome da rota da v1 ('julgados_acordaos_LA'); sem ele, pelo código da unidade.
export function unidadeJulgados(data: Pick<JulgadosAcordaosResponse, 'dashboard' | 'meta'>): JulgadosUnit | null {
    const rota = /^julgados_acordaos_(NG|LA|RJ)$/.exec(data.dashboard ?? '')
    if (rota) return rota[1] as JulgadosUnit
    return isJulgadosUnit(data.meta.unit) ? data.meta.unit : null
}

export type JulgadosFields = {
    numeros: Record<JulgadosNumero, string | null>
    comparativos: Record<JulgadosComparavel, string | null>
    listas: Record<JulgadosLista, string | null> // 'stats.x' = dentro de stats
}

// Os nomes dos campos na unidade; null = não existe nessa unidade (ou unidade desconhecida).
export function julgadosFields(unit: JulgadosUnit | null): JulgadosFields {
    const nome = (chave: string, base: string) => (unit && !FALTA[unit].includes(chave) ? `${base}_${unit}` : null)
    const numeros = {} as Record<JulgadosNumero, string | null>
    for (const k of JULGADOS_NUMEROS) numeros[k] = nome(k, NUMEROS[k])
    const comparativos = {} as Record<JulgadosComparavel, string | null>
    for (const k of COMPARAVEIS) comparativos[k] = nome(k, `comparativo_${NUMEROS[k]}`)
    const listas = {} as Record<JulgadosLista, string | null>
    for (const k of JULGADOS_LISTAS) listas[k] = nome(k, LISTAS[k])
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

function relatores(v: unknown): LinhaRelator[] {
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

function linhas(v: unknown): LinhaAcordao[] {
    return objetos(v).map((r) => ({
        id: numero(r.id),
        numero_processo: texto(r.numero_processo),
        fase: texto(r.fase),
        subfase: texto(r.subfase),
        status_2g: texto(r.status_2g),
        uf: texto(r.uf),
        relator: texto(r.relator),
        data_acordao: dia(r.data_acordao),
        status_acordao_embargos: texto(r.status_acordao_embargos),
        data_acordao_embargos: dia(r.data_acordao_embargos),
    }))
}

function faltando(v: unknown): DadoFaltando[] {
    return objetos(v)
        .map((r) => ({ numero_processo: texto(r.numero_processo), campo: texto(r.campo) }))
        .filter((r) => r.campo !== '')
}

export type JulgadosAcordaos = {
    unit: JulgadosUnit | null
    n: Record<JulgadosNumero, number | null>
    comparativo: Record<JulgadosComparavel, number | null>
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
    lista: LinhaAcordao[]
    // Estudo das Improcedências, nos dois escopos (entrada no período e estoque).
    improcedencia: Record<
        Escopo,
        { porComarca: PontoJulgados[]; porMotivo: PontoJulgados[]; porRelator: PontoJulgados[] }
    >
}

export type Escopo = 'entrada' | 'estoque'

// A resposta numa forma só, com os nomes da unidade certa.
export function lerJulgadosAcordaos(resp: JulgadosAcordaosResponse): JulgadosAcordaos {
    const unit = unidadeJulgados(resp)
    const f = julgadosFields(unit)
    const stats = resp.stats ?? {}
    const bruto = (campo: string | null): unknown => {
        if (!campo) return undefined
        return campo.startsWith('stats.') ? stats[campo.slice(6)] : resp[campo]
    }
    const deStats = (campo: string | null) => (campo ? stats[campo] : undefined)
    const n = {} as Record<JulgadosNumero, number | null>
    for (const k of JULGADOS_NUMEROS) n[k] = numero(deStats(f.numeros[k]))
    const comparativo = {} as Record<JulgadosComparavel, number | null>
    for (const k of COMPARAVEIS) comparativo[k] = numero(deStats(f.comparativos[k]))
    const lista = (k: JulgadosLista) => pontos(bruto(f.listas[k]))

    return {
        unit,
        n,
        comparativo,
        ufOpcoes: textos(bruto(f.listas.ufOpcoes)).map((u) => u.trim().toUpperCase()),
        comarcaOpcoes: textos(bruto(f.listas.comarcaOpcoes)),
        dadosFaltando: faltando(bruto(f.listas.dadosFaltando)),
        ranking: relatores(bruto(f.listas.ranking)),
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
        improcedencia: {
            entrada: {
                porComarca: lista('improcedenciaPorComarca'),
                porMotivo: lista('improcedenciaPorMotivo'),
                porRelator: lista('improcedenciaPorRelator'),
            },
            estoque: {
                porComarca: lista('improcedenciaPorComarcaEstoque'),
                porMotivo: lista('improcedenciaPorMotivoEstoque'),
                porRelator: lista('improcedenciaPorRelatorEstoque'),
            },
        },
    }
}
