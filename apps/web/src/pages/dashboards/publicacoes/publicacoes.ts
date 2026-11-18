import type { CommissionTable } from '../../../lib/commissionReport.ts'
import type { Meta, Point } from '../../../types/index.ts'

// Publicações (LexFlow, NG/LA/RJ): as páginas da v1 NG/PublicacoesNG.tsx, LA/PublicacoesLA.tsx e RJ/PublicacoesRJ.tsx.
// A API devolve a chamada do período da rota da v1 (só os campos usados, com os nomes da NG), os leitores de todo
// o histórico e a comissão (app/dashboards/publicacoes.py); aqui as contas que a página da v1 fazia no navegador.
// Só lógica pura (testada em publicacoes.test.ts).

export type PublicacoesResponse = {
    meta: Meta
    unidade?: 'NG' | 'LA' | 'RJ'
    stats?: Record<string, unknown>
    leitores?: string[]
    comissao?: unknown
} & Record<string, unknown>

const objetos = (v: unknown): Record<string, unknown>[] =>
    Array.isArray(v) ? v.filter((x): x is Record<string, unknown> => typeof x === 'object' && x !== null) : []
const texto = (v: unknown) => (v === null || v === undefined ? '' : String(v).trim())
export const numero = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)
const n0 = (v: unknown) => numero(v) ?? 0
const pontos = (v: unknown): Point[] => objetos(v).map((p) => ({ name: texto(p.name), value: n0(p.value) }))
const desc = (xs: Point[]) => [...xs].sort((a, b) => b.value - a.value)

// A meta da taxa de resolução que libera a comissão (v1: THRESHOLD = 98).
export const META_RESOLUCAO = 98

// '2026-11-18' -> Date local (sem fuso).
const dataLocal = (iso: string) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso)
    return m ? new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3])) : null
}
const isoLocal = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

// A linha do tempo da v1 (publicacoesDiariasSpline): um ponto por dia do período, com Chegadas, Cumpridas,
// Visualizadas (NG e RJ) e "Atraso em dias". Como a v1, o atraso não é uma contagem: no dia D vale (dia de
// referência − D) quando ainda há pendente que chegou em D (vem do histograma de pendentes por dias de atraso).
export function linhaDoTempo(data: PublicacoesResponse, de: string, ate: string) {
    const ini = dataLocal(de)
    const fim = dataLocal(ate)
    const dias: string[] = []
    if (ini && fim) for (let d = new Date(ini); d <= fim; d.setDate(d.getDate() + 1)) dias.push(isoLocal(d))
    const mapa = (v: unknown) => new Map(pontos(v).map((p) => [p.name.slice(0, 10), p.value]))
    const recebidas = mapa(data.publicacoes_recebidas_por_dia_NG)
    const cumpridas = mapa(data.publicacoes_tratadas_por_dia_NG)
    const visualizadas = mapa(data.publicacoes_visualizadas_por_dia_NG)
    const ref = dataLocal(texto(data.stats?.dia_referencia_publicacoes_NG)) ?? fim
    const atraso = new Map<string, number>()
    for (const p of pontos(data.publicacoes_pendentes_por_dias_atraso_NG)) {
        const k = Number(p.name)
        if (!ref || !Number.isInteger(k) || k < 0 || p.value <= 0) continue
        const chegada = new Date(ref)
        chegada.setDate(chegada.getDate() - k)
        if (!atraso.has(isoLocal(chegada))) atraso.set(isoLocal(chegada), k)
    }
    const temVisualizadas = Array.isArray(data.publicacoes_visualizadas_por_dia_NG)
    const serie = (m: Map<string, number>) => dias.map((d) => m.get(d) ?? 0)
    const series = [
        { label: 'Chegadas', values: serie(recebidas) },
        { label: 'Cumpridas', values: serie(cumpridas) },
        ...(temVisualizadas ? [{ label: 'Visualizadas', values: serie(visualizadas) }] : []),
        { label: 'Atraso em dias', values: serie(atraso) },
    ]
    return { dias, series, temDados: series.some((s) => s.values.some((v) => v !== 0)) }
}

// "Demandas por funcionário" da v1: pendentes (estoque de agora) + cumpridas no período, por leitor.
export function demandas(data: PublicacoesResponse) {
    const por = new Map<string, { name: string; pendentes: number; cumpridas: number }>()
    for (const p of pontos(data.publicacoes_pendentes_por_leitor_NG)) {
        const n = p.name || '—'
        por.set(n, { name: n, pendentes: p.value, cumpridas: 0 })
    }
    for (const p of pontos(data.publicacoes_cumprido_por_leitor_NG)) {
        const n = p.name || '—'
        const r = por.get(n) ?? { name: n, pendentes: 0, cumpridas: 0 }
        r.cumpridas = p.value
        por.set(n, r)
    }
    return [...por.values()]
        .map((r) => ({ ...r, total: r.pendentes + r.cumpridas }))
        .filter((r) => r.total > 0)
        .sort((a, b) => b.total - a.total)
}

// Taxa de resolução da v1: cumpridas no período ÷ recebidas no período (comissiona a partir de 98%).
export function resolucao(recebidas: number, cumpridas: number) {
    const temDados = recebidas > 0
    const taxa = temDados ? (cumpridas / recebidas) * 100 : 0
    return {
        temDados,
        taxa,
        naoCumpridas: Math.max(recebidas - cumpridas, 0),
        comissiona: temDados && taxa >= META_RESOLUCAO,
        pctCumpridas: temDados ? Math.min((cumpridas / recebidas) * 100, 100) : 0,
        pctNaoCumpridas: temDados ? Math.min((Math.max(recebidas - cumpridas, 0) / recebidas) * 100, 100) : 0,
    }
}

// Duração da v1 (formatDuration, em horas): '0h', '35min', '5h 15min', '2d 3h'.
export function duracaoHoras(horas: number): string {
    if (!horas) return '0h'
    if (horas < 1) return `${Math.round(horas * 60)}min`
    if (horas < 24) {
        const h = Math.floor(horas)
        const m = Math.round((horas - h) * 60)
        return m > 0 ? `${h}h ${m}min` : `${h}h`
    }
    const d = Math.floor(horas / 24)
    const r = Math.floor(horas % 24)
    return r > 0 ? `${d}d ${r}h` : `${d}d`
}

// O valor de status_agendamento da v1 a partir da fatia clicada ("Sem agendamento" -> sem; o resto -> com).
export const statusAgendamento = (fatia: string) => (fatia.trim().toLowerCase().startsWith('sem') ? 'sem' : 'com')

export type Publicacao = {
    id: string
    status: string
    documento: string
    materia: string
    leitor: string
    setor: string // NG/RJ: o agendamento depois da conclusão; LA: TRIBUNAL - ÓRGÃO
    recebidaEm: string | null
}

export function lerPublicacoes(data: PublicacoesResponse) {
    const s = data.stats ?? {}
    const n = (k: string) => numero(s[k])
    const com = n0(s.publicacoes_com_agendamento_apos_finalizacao_NG)
    const sem = n0(s.publicacoes_sem_agendamento_apos_finalizacao_NG)
    return {
        unidade: data.unidade ?? 'NG',
        temDados: data.stats !== undefined,
        recebidas: n('publicacoes_recebidas_periodo_NG'),
        recebidasHoje: n('publicacoes_recebidas_hoje_NG'),
        cumpridas: n('publicacoes_tratadas_periodo_NG'),
        pendentes: n('publicacoes_pendentes_NG'),
        tempoMedioDias: n('media_tempo_tratamento_publicacoes_NG'),
        zeradas: n('publicacoes_pendentes_zeradas_no_periodo_NG'),
        diaReferencia: texto(s.dia_referencia_publicacoes_NG) || null,
        cumpridasDiaRef: n('publicacoes_tratadas_ultimo_dia_NG'),
        recebidasDiaRef: n('publicacoes_recebidas_dia_referencia_NG'),
        mesmoDia: n('publicacoes_cumpridas_mesmo_dia_dia_referencia_NG'),
        pctMesmoDia: n('pct_tratadas_mesmo_dia_publicacoes_NG'),
        comDataDisponibilizacao: n('publicacoes_com_data_disponibilizacao_NG'),
        mesmoDiaTotal: n('publicacoes_cumpridas_mesmo_dia_chegada_NG'),
        agendamento: { com, sem, pct: com + sem > 0 ? (com / (com + sem)) * 100 : null },
        porMateria: desc(pontos(data.publicacoes_por_materia_NG)),
        porDocumento: desc(pontos(data.publicacoes_por_tipo_documento_NG)),
        porTribunal: desc(pontos(data.publicacoes_por_tribunal_NG)),
        porOrgao: desc(pontos(data.publicacoes_por_orgao_NG)),
        porAtividade: desc(pontos(data.publicacoes_agendamento_apos_finalizacao_por_atividade_NG)),
        porSetor: desc(pontos(data.publicacoes_agendamento_apos_finalizacao_por_setor_NG)),
        demandas: demandas(data),
        leitores: Array.isArray(data.leitores) ? data.leitores.map(texto).filter(Boolean) : [],
        lista: objetos(data.publicacoes_lista_NG).map((r, i): Publicacao => ({
            id: texto(r.id) || String(i),
            status: texto(r.status) || '—',
            documento: texto(r.descricao),
            materia: texto(r.operacao) || texto(r.atividade),
            leitor: texto(r.funcionario_atribuido) || texto(r.funcionario),
            setor: texto(r.pessoa_setor),
            recebidaEm: texto(r.criado_em) || null,
        })),
    }
}

// --- Comissão (v1: ComissionamentoPdf, "Comissionamento — Publicações <u>"): R$ 0,20 por certa, R$ 0,50 por errada ---

const brl = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const inteiro = (v: number) => v.toLocaleString('pt-BR')

export function comissaoPublicacoes(data: PublicacoesResponse): CommissionTable | undefined {
    if (!Array.isArray(data.comissao)) return undefined
    return {
        title: `Comissionamento — Publicações ${data.unidade ?? 'NG'}`,
        columns: [
            { key: 'funcionario', label: 'Funcionários' },
            { key: 'qtd_lidas', label: 'Qtd lidas', format: inteiro, sum: true },
            { key: 'qtd_certas', label: 'Qtd certas', format: inteiro, sum: true },
            { key: 'qtd_erradas', label: 'Qtd erradas', format: inteiro, sum: true },
            { key: 'valor_certa', label: 'Valor certa', format: brl },
            { key: 'valor_errada', label: 'Valor errada', format: brl },
            { key: 'comissao', label: 'Comissão', format: brl, sum: true },
        ],
        rows: objetos(data.comissao).map((r) => ({
            funcionario: texto(r.funcionario),
            qtd_lidas: numero(r.qtd_lidas),
            qtd_certas: numero(r.qtd_certas),
            qtd_erradas: numero(r.qtd_erradas),
            valor_certa: numero(r.valor_certa),
            valor_errada: numero(r.valor_errada),
            comissao: numero(r.comissao),
        })),
        sortBy: 'comissao',
    }
}
