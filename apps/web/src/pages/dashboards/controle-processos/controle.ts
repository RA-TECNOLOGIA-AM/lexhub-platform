import type { FilterField } from '../../../lib/filters.ts'
import type { DashboardFilters, Meta, Point } from '../../../types/index.ts'

// Controle de Processos (NG, LA e RJ): a página da v1 NG/ControleProcessos.tsx (LA pela rota da v1 dele; RJ com o
// cálculo do NG no escritório do RJ). A API (app/dashboards/controle_processos.py)
// faz as chamadas da v1 (controle no período, no histórico e na fase; Protocolo legado; Protocolo LexPre; Execução e
// Acordos) e devolve só os campos usados; as somas da esteira ficam aqui, como na v1. Só lógica pura (controle.test.ts).

type Bloco = Record<string, unknown> | null | undefined

export type ControleResponse = {
    meta: Meta
    unidade?: string
    tem_uf?: boolean // false = a rota do controle da unidade não filtra por UF (LA, como a v1)
    periodo?: Bloco
    historico?: Bloco
    fase?: Bloco
    protocolo?: Bloco
    lexpre?: Bloco
    execucao?: Bloco
}

export type QtdValor = { qtd: number | null; valor: number | null }
export type TipoSentenca = { tipo: string; qtd: number; valor: number | null }
export type Subfase = { name: string; value: number; valor: number | null; tempoMedioDias: number | null }
export type Tempo = { valor: number | null; comparativo: number | null }

export type Controle = {
    temDados: boolean
    situacao: 'ativo' | 'suspenso' | null
    total: QtdValor
    protocolados: QtdValor
    inicial: QtdValor
    inicialIndeferida: QtdValor
    recursal: QtdValor
    recursalNaoProvido: QtdValor
    transitoJulgado: QtdValor
    execucao: QtdValor
    arquivadosProcedencia: QtdValor
    extintos1g: { comMerito: QtdValor; semMerito: QtdValor; porTipo: TipoSentenca[]; total: number }
    extintos2g: {
        comMerito: QtdValor
        semMerito: QtdValor
        porTipo: TipoSentenca[]
        total: number
        taxaProvimento: number | null // % de acórdãos providos no período
    }
    improcedencia: QtdValor
    totalExtintos: number
    carteiraLiquida: number
    // De onde vem o tempo do Protocolo: o banco NG legado (contratação → saída do protocolo) e/ou o LexPre (entrada →
    // saída do setor de Protocolo; não tem a data de contratação). null = nenhum dos dois teve protocolo no período.
    fonteProtocolo: 'legado' | 'lexpre' | 'ambos' | null
    permanencia: {
        protocolo: { media: Tempo; mediana: Tempo }
        inicial: { media: Tempo; mediana: Tempo }
        recursal: { media: Tempo; mediana: Tempo }
        execucao: { media: Tempo; mediana: Tempo }
    }
    porMes: { inicial: Point[]; recursal: Point[]; execucao: Point[] }
    fases: string[] // opções do seletor de fase (maior primeiro)
    ufs: string[]
    subfases: { itens: Subfase[]; total: number | null; qtd: number | null } | null // null = sem fase escolhida
}

const numero = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)
const n0 = (v: unknown) => numero(v) ?? 0
const texto = (v: unknown) => (typeof v === 'string' ? v.trim() : v == null ? '' : String(v).trim())
const obj = (v: unknown): Record<string, unknown> =>
    typeof v === 'object' && v !== null ? (v as Record<string, unknown>) : {}
const objetos = (v: unknown): Record<string, unknown>[] =>
    Array.isArray(v) ? v.filter((x): x is Record<string, unknown> => typeof x === 'object' && x !== null) : []
const pontos = (v: unknown): Point[] =>
    objetos(v)
        .map((p) => ({ name: texto(p.name), value: n0(p.value) }))
        .filter((p) => p.name)

// As linhas "por tipo de sentença / acórdão" (normalizeSentencaRows da v1), da maior quantidade para a menor.
function porTipo(v: unknown): TipoSentenca[] {
    return objetos(v)
        .map((r) => ({
            tipo: texto(r.tipo_sentenca) || texto(r.label),
            qtd: n0(r.quantidade),
            valor: numero(r.valor_causa),
        }))
        .filter((r) => r.tipo)
        .sort((a, b) => b.qtd - a.qtd)
}

// Metas dos gráficos "mês a mês" da v1: a média dos limites do JEC e da Vara Cível, em dias.
export const METAS_DIAS = { inicial: 275, recursal: 135, execucao: 210 } as const

export function lerControle(data: ControleResponse, filters: DashboardFilters = {}): Controle {
    const P = obj(data.periodo) // controle com o período
    const H = obj(data.historico) // controle sem período
    const pr = obj(data.protocolo) // Protocolo do banco NG legado
    const lx = obj(data.lexpre) // Protocolo LexPre
    const ex = obj(data.execucao) // Execução e Acordos
    const c = (k: string) => `controle_processo_${k}_NG`
    const qv = (fonte: Record<string, unknown>, qtd: string, valor: string): QtdValor => ({
        qtd: numero(fonte[qtd]),
        valor: numero(fonte[valor]),
    })
    const situacaoRaw = texto(filters.situacao_controle?.[0]).toLowerCase()
    const situacao = situacaoRaw === 'ativo' || situacaoRaw === 'suspenso' ? situacaoRaw : null
    const suspenso = situacao === 'suspenso' // v1: protocolados e execução são sempre ativos

    const protocolados: QtdValor = suspenso
        ? { qtd: 0, valor: 0 }
        : {
              qtd: n0(pr.protocolos_resolvidos) + n0(lx.protocolados_total),
              valor: n0(pr.valor_causa_protocolo_novo) + n0(lx.valor_causa_protocolado),
          }
    const execucao: QtdValor = suspenso
        ? { qtd: 0, valor: 0 }
        : {
              qtd: n0(ex.total_em_execucao) + n0(ex.total_em_execucao_acordos_NG),
              valor: n0(ex.valor_total_em_execucao) + n0(ex.valor_total_em_execucao_acordos_NG),
          }
    // v1: a quantidade soma Condenação e Acordos; o valor é só o TED da Condenação ("TED só existe na Condenação").
    const arquivadosProcedencia: QtdValor = {
        qtd: n0(ex.total_saida_execucao_periodo) + n0(ex.total_saida_execucao_acordos_periodo_NG),
        valor: n0(ex.valor_ted_saida_execucao_periodo),
    }

    const com1 = qv(P, c('extintos_com_merito_qtd'), c('extintos_com_merito_valor_causa'))
    const sem1 = qv(P, c('extintos_sem_merito_qtd'), c('extintos_sem_merito_valor_causa'))
    const com2 = qv(P, c('extintos_com_merito_2g_qtd'), c('extintos_com_merito_2g_valor_causa'))
    const sem2 = qv(P, c('extintos_sem_merito_2g_qtd'), c('extintos_sem_merito_2g_valor_causa'))
    const total1 = n0(com1.qtd) + n0(sem1.qtd)
    const total2 = n0(com2.qtd) + n0(sem2.qtd)

    const tempo = (fonte: Record<string, unknown>, valor: string, comparativo: string): Tempo => ({
        valor: numero(fonte[valor]),
        comparativo: numero(fonte[comparativo]),
    })
    const fase = (nome: 'inicial' | 'recursal' | 'execucao') => ({
        media: tempo(P, c(`fase_${nome}_media_dias`), c(`fase_${nome}_comparativo_media_dias`)),
        mediana: tempo(P, c(`fase_${nome}_mediana_dias`), c(`fase_${nome}_comparativo_mediana_dias`)),
    })

    const F = data.fase ? obj(data.fase) : null
    const protocolo = tempoProtocolo(pr, lx)
    return {
        temDados: Object.keys(H).length > 0,
        situacao,
        total: qv(H, 'total_controle_processo_NG', c('valor_causa_total')),
        protocolados,
        inicial: qv(H, c('fase_inicial_qtd'), c('fase_inicial_valor_causa')),
        inicialIndeferida: qv(H, c('log_inicial_indeferida_qtd'), c('log_inicial_indeferida_valor_causa')),
        recursal: qv(H, c('fase_recursal_qtd'), c('fase_recursal_valor_causa')),
        recursalNaoProvido: qv(H, c('log_recursal_nao_provido_qtd'), c('log_recursal_nao_provido_valor_causa')),
        transitoJulgado: qv(H, c('fase_transito_julgado_qtd'), c('fase_transito_julgado_valor_causa')),
        execucao,
        arquivadosProcedencia,
        extintos1g: {
            comMerito: com1,
            semMerito: sem1,
            porTipo: porTipo(P[c('extintos_com_merito_por_tipo_sentenca')]),
            total: total1,
        },
        extintos2g: {
            comMerito: com2,
            semMerito: sem2,
            porTipo: porTipo(P[c('extintos_com_merito_2g_por_tipo_sentenca')]),
            total: total2,
            taxaProvimento: numero(P[c('taxa_provimento_2g')]),
        },
        improcedencia: qv(P, c('fase_arquivado_improcedente_qtd'), c('fase_arquivado_improcedente_valor_causa')),
        totalExtintos: total1 + total2,
        carteiraLiquida: n0(protocolados.valor) - n0(sem1.valor) - n0(sem2.valor),
        fonteProtocolo: protocolo.fonte,
        permanencia: {
            protocolo: { media: protocolo.media, mediana: protocolo.mediana },
            inicial: fase('inicial'),
            recursal: fase('recursal'),
            execucao: fase('execucao'),
        },
        porMes: {
            inicial: pontos(H[c('fase_inicial_media_dias_por_mes')]),
            recursal: pontos(H[c('fase_recursal_media_dias_por_mes')]),
            execucao: pontos(H[c('fase_execucao_media_dias_por_mes')]),
        },
        fases: pontos(H[c('por_fase')])
            .sort((a, b) => b.value - a.value)
            .map((p) => p.name),
        ufs: Array.isArray(H[c('uf_opcoes')]) ? (H[c('uf_opcoes')] as unknown[]).map(texto).filter(Boolean) : [],
        subfases: F
            ? {
                  itens: objetos(F[c('por_subfase')])
                      .map((s) => ({
                          name: texto(s.name),
                          value: n0(s.value),
                          valor: numero(s.valor_causa),
                          tempoMedioDias: numero(s.tempo_medio_dias),
                      }))
                      .filter((s) => s.name)
                      .sort((a, b) => b.value - a.value),
                  total: numero(F[c('total_na_fase')]),
                  qtd: numero(F[c('qtd_subfases_na_fase')]),
              }
            : null,
    }
}

// O tempo do Protocolo com os dois bancos (a v1 só lia o legado, que hoje não recebe mais protocolos): só um com
// protocolos no período = o dele; os dois = média ponderada pela quantidade de cada um, e a mediana e a variação do
// que teve mais protocolos (não dá para juntar medianas); nenhum = sem valor (em vez de "0h / -100%").
export function tempoProtocolo(
    legado: Record<string, unknown>,
    lexpre: Record<string, unknown>,
): { fonte: Controle['fonteProtocolo']; media: Tempo; mediana: Tempo } {
    const nL = n0(legado.protocolos_resolvidos)
    const nX = n0(lexpre.protocolados_total)
    const doLegado = {
        media: {
            valor: numero(legado.tempo_medio_contratacao_protocolo),
            comparativo: numero(legado.comparativo_tempo_medio_contratacao_protocolo),
        },
        mediana: {
            valor: numero(legado.mediana_tempo_contratacao_protocolo),
            comparativo: numero(legado.comparativo_mediana_tempo_contratacao_protocolo),
        },
    }
    const doLexpre = {
        media: {
            valor: numero(lexpre.media_tempo_protocolado),
            comparativo: numero(lexpre.comparativo_tempo_medio_protocolado),
        },
        mediana: {
            valor: numero(lexpre.mediana_tempo_protocolado),
            comparativo: numero(lexpre.comparativo_mediana_tempo_protocolado),
        },
    }
    if (!nL && !nX) {
        return { fonte: null, media: { valor: null, comparativo: null }, mediana: { valor: null, comparativo: null } }
    }
    if (!nX) return { fonte: 'legado', ...doLegado }
    if (!nL) return { fonte: 'lexpre', ...doLexpre }
    const maior = nX >= nL ? doLexpre : doLegado
    const media =
        doLegado.media.valor !== null && doLexpre.media.valor !== null
            ? (doLegado.media.valor * nL + doLexpre.media.valor * nX) / (nL + nX)
            : maior.media.valor
    return { fonte: 'ambos', media: { valor: media, comparativo: maior.media.comparativo }, mediana: maior.mediana }
}

// Dias com horas, como a v1 (formatPermanenciaFromDays): "204d 11h", "5h", "45min"; sem valor = "—".
export function duracao(dias: number | null): string {
    if (dias === null) return '—'
    const horas = dias * 24
    if (horas <= 0) return '0h'
    if (horas < 1) return `${Math.round(horas * 60)}min`
    if (horas < 24) {
        const h = Math.floor(horas)
        const min = Math.round((horas - h) * 60)
        return min ? `${h}h ${min}min` : `${h}h`
    }
    const d = Math.floor(horas / 24)
    const h = Math.floor(horas - d * 24)
    return h ? `${d}d ${h}h` : `${d}d`
}

export const SITUACOES_CONTROLE = [
    { value: 'ativo', label: 'Somente ativos' },
    { value: 'suspenso', label: 'Somente Suspenso/sobrestado' },
]

// Os filtros da v1: a situação (uma; sem = as duas) e as UFs (várias). A fase é o seletor do próprio gráfico.
export function filtrosControle(data: ControleResponse, f: DashboardFilters = {}): FilterField[] {
    const c = lerControle(data, f)
    if (!c.temDados) return []
    const ufs = [...new Set([...c.ufs, ...(f.uf_controle ?? [])])]
    return [
        { key: 'situacao_controle', label: 'Situação', options: SITUACOES_CONTROLE, single: true },
        ...(data.tem_uf === false
            ? []
            : [{ key: 'uf_controle' as const, label: 'UF', options: ufs.map((u) => ({ value: u, label: u })) }]),
        {
            key: 'fase_controle',
            label: 'Fase',
            options: [...new Set([...c.fases, ...(f.fase_controle ?? [])])].map((v) => ({ value: v, label: v })),
            single: true,
            inline: true,
        },
    ]
}
