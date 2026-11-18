import type { CommissionTable } from '../../../lib/commissionReport.ts'
import type { DashboardFilters, Meta, Point } from '../../../types/index.ts'
import {
    opcoesLista,
    tarefas,
    type DemandaFuncionario,
    type OpcoesLista,
    type Tarefa,
} from '../execucao/setorExecucao.ts'

// Recursal (LexFlow, NG/LA/RJ): as páginas da v1 NG/Recursal.tsx, LA/Recursal_LA.tsx e RJ/Recursal_RJ.tsx. A API
// junta as chamadas que a página da v1 fazia (app/dashboards/recursal.py), sempre com os nomes da NG; aqui só a
// leitura e as contas que a página fazia no navegador. Só lógica pura (testada em recursal.test.ts).

type Bloco = { stats?: Record<string, unknown> } & Record<string, unknown>
type Base = 'estoque' | 'entrada'

export type RecursalResponse = {
    meta: Meta
    unidade?: 'NG' | 'LA' | 'RJ'
    periodo?: Bloco
    historico?: Bloco
    producao?: Bloco
    subfase?: Record<Base, Bloco>
    materia?: Record<Base, Bloco>
    competencia?: Record<Base, Bloco>
    vara?: Record<Base, Bloco>
    decisoes?: Bloco
    status_1g?: Bloco
    status_2g?: Bloco
    juizes?: Bloco
    relatores?: Bloco
    controle?: Bloco
    opcoes?: Record<string, unknown>
    comissao?: Record<string, unknown> | null // só NG e só para quem vê a comissão (app/dashboards/recursal_export.py)
}

// --- leitura solta ---
const obj = (v: unknown): Record<string, unknown> =>
    typeof v === 'object' && v !== null && !Array.isArray(v) ? (v as Record<string, unknown>) : {}
const objetos = (v: unknown): Record<string, unknown>[] =>
    Array.isArray(v) ? v.filter((x): x is Record<string, unknown> => typeof x === 'object' && x !== null) : []
const texto = (v: unknown) => (v === null || v === undefined ? '' : String(v).trim())
export const numero = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)
const n0 = (v: unknown) => numero(v) ?? 0
const textos = (v: unknown) => (Array.isArray(v) ? v.map(texto).filter(Boolean) : [])
const st = (b: Bloco | undefined) => obj(b?.stats)

export type Linha = {
    name: string
    value: number
    valorCausa: number | null
    percent: number | null
    id: number | null
}
const linhas = (v: unknown, campoId?: 'id_1g' | 'id_2g'): Linha[] =>
    objetos(v).map((r) => ({
        name: texto(r.name),
        value: n0(r.value),
        valorCausa: numero(r.valor_causa),
        percent: numero(r.percent),
        id: campoId ? numero(r[campoId]) : null,
    }))
const desc = <T extends { value: number }>(xs: T[]) => [...xs].sort((a, b) => b.value - a.value)

// --- decisões (os cards e a matriz 1º × 2º grau) ---

// O id do card (o nome dos campos de stats) e o valor do filtro na API (a v1 mandava 'extincao_reajuizar', que a
// rota recusa: o certo é 'extincao_permite_reajuizar').
export const DECISOES = [
    { key: 'mantido_ganho', label: 'Mantido Ganho', tone: 'ok' },
    { key: 'ganho_ampliado', label: 'Ganho Ampliado', tone: 'ok' },
    { key: 'revertido_ganho', label: 'Revertido Ganho', tone: 'ok' },
    { key: 'ganho_reduzido', label: 'Ganho Reduzido', tone: 'warn' },
    { key: 'mantido_perda', label: 'Mantido Perda', tone: 'danger' },
    { key: 'revertido_perda', label: 'Revertido Perda', tone: 'danger' },
    { key: 'instrucao_retomada', label: 'Instrução Retomada', tone: 'info' },
    { key: 'extincao_reajuizar', label: 'Extinção (Permite Reajuizar)', tone: 'warn' },
] as const
export type ChaveDecisao = (typeof DECISOES)[number]['key']
export const filtroDecisao = (k: ChaveDecisao) => (k === 'extincao_reajuizar' ? 'extincao_permite_reajuizar' : k)

// A matriz de classificação da v1 (linhas = mérito 1G, colunas = mérito 2G) e os ids de status que a célula filtra.
export const MATRIZ_1G = [
    'PROCEDENTE (COM PE)',
    'PROCEDENTE (SEM PE)',
    'PARC. PROCEDENTE (COM PE)',
    'PARC. PROCEDENTE (SEM PE)',
    'IMPROCEDENTE',
    'IMPROCEDENTE POR PRESCRIÇÃO',
    'EXTINTO SEM MÉRITO',
]
export const MATRIZ_2G = [...MATRIZ_1G, 'SENTENÇA ANULADA']
const G = 'revertido_ganho'
export const MATRIZ: ChaveDecisao[][] = [
    [
        'mantido_ganho',
        'ganho_reduzido',
        'ganho_reduzido',
        'ganho_reduzido',
        'revertido_perda',
        'revertido_perda',
        'extincao_reajuizar',
        'instrucao_retomada',
    ],
    [
        'ganho_ampliado',
        'mantido_ganho',
        'ganho_reduzido',
        'ganho_reduzido',
        'revertido_perda',
        'revertido_perda',
        'extincao_reajuizar',
        'instrucao_retomada',
    ],
    [
        'ganho_ampliado',
        'ganho_ampliado',
        'mantido_ganho',
        'ganho_reduzido',
        'revertido_perda',
        'revertido_perda',
        'extincao_reajuizar',
        'instrucao_retomada',
    ],
    [
        'ganho_ampliado',
        'ganho_ampliado',
        'ganho_ampliado',
        'mantido_ganho',
        'revertido_perda',
        'revertido_perda',
        'extincao_reajuizar',
        'instrucao_retomada',
    ],
    [G, G, G, G, 'mantido_perda', 'mantido_perda', 'extincao_reajuizar', 'instrucao_retomada'],
    [G, G, G, G, 'mantido_perda', 'mantido_perda', 'extincao_reajuizar', 'instrucao_retomada'],
    [G, G, G, G, 'revertido_perda', 'revertido_perda', 'extincao_reajuizar', 'instrucao_retomada'],
]
const IDS_1G = [[20], [22], [21], [23], [19], [], [18]]
const IDS_2G = [[21], [24], [20], [25], [19], [], [18], [22]]

const mesmos = (a: string[] = [], b: string[]) => a.length === b.length && b.every((x) => a.includes(x))

// A célula marcada: a decisão dela sozinha e os status 1G/2G da linha e da coluna (v1: a mesma regra).
export function celulaMarcada(f: DashboardFilters, linha: number, coluna: number): boolean {
    const dec = filtroDecisao(MATRIZ[linha][coluna])
    return (
        mesmos(f.decisao_recursal, [dec]) &&
        mesmos(f.id_1g_recursal, IDS_1G[linha].map(String)) &&
        mesmos(f.id_2g_recursal, IDS_2G[coluna].map(String))
    )
}

// Clicar numa célula: troca status 1G, status 2G e decisão pelos dela; de novo, tira os três.
export function clicarCelula(f: DashboardFilters, linha: number, coluna: number): DashboardFilters {
    const novo: DashboardFilters = { ...f }
    delete novo.decisao_recursal
    delete novo.id_1g_recursal
    delete novo.id_2g_recursal
    if (celulaMarcada(f, linha, coluna)) return novo
    novo.decisao_recursal = [filtroDecisao(MATRIZ[linha][coluna])]
    if (IDS_1G[linha].length) novo.id_1g_recursal = IDS_1G[linha].map(String)
    if (IDS_2G[coluna].length) novo.id_2g_recursal = IDS_2G[coluna].map(String)
    return novo
}

// --- rankings de juízes e relatores ---

export type Magistrado = {
    name: string
    initials: string
    total: number
    taxa: number
    fav: number
    des: number
    outros: number
    pFav: number
    pDes: number
    pOutros: number
}
const ranking = (v: unknown): Magistrado[] =>
    objetos(v).map((r) => ({
        name: texto(r.name),
        initials: texto(r.initials) || texto(r.name).slice(0, 2).toUpperCase(),
        total: n0(r.total_casos),
        taxa: n0(r.taxa_sucesso),
        fav: n0(r.fav),
        des: n0(r.des),
        outros: n0(r.outros),
        pFav: n0(r.percent_fav),
        pDes: n0(r.percent_des),
        pOutros: n0(r.percent_outros),
    }))
// A cor da taxa de sucesso da v1: ≥ 60 verde, ≥ 45 amarelo, abaixo vermelho.
export const tomTaxa = (t: number) => (t >= 60 ? 'ok' : t >= 45 ? 'warn' : 'danger')

// --- Extintos 2º grau ---

export type PorTipo = { tipo: string; qtd: number; valor: number | null }
// v1: normalizeExtintosPorTipoRows (lista de objetos ou objeto {tipo: qtd}).
export function porTipo(v: unknown): PorTipo[] {
    if (Array.isArray(v)) {
        return objetos(v)
            .map((r) => ({
                tipo: texto(r.tipo_sentenca ?? r.label ?? r.tipo ?? r.name),
                qtd: n0(r.quantidade ?? r.qtd ?? r.value),
                valor: numero(r.valor_causa ?? r.valor ?? r.valorCausa ?? r.amount),
            }))
            .filter((r) => r.tipo)
    }
    return Object.entries(obj(v)).map(([tipo, x]) =>
        typeof x === 'number'
            ? { tipo, qtd: x, valor: null }
            : {
                  tipo,
                  qtd: n0(obj(x).quantidade ?? obj(x).qtd ?? obj(x).value),
                  valor: numero(obj(x).valor_causa ?? obj(x).valor),
              },
    )
}

// --- produção (histórico todo, sem filtros, como a v1) ---

// v1 aggregateDaily: um funcionário = a série dele; vários = a soma; nenhum = a do setor (ou a soma de todos).
export function producaoDias(producao: Bloco | undefined, funcionarios: string[]): Point[] {
    const porFunc = obj(producao?.recursal_resolvidos_por_dia_por_funcionario_NG)
    const serie = (nome: string) => objetos(porFunc[nome]).map((p) => ({ name: texto(p.name), value: n0(p.value) }))
    const soma = (nomes: string[]) => {
        const m = new Map<string, number>()
        for (const n of nomes) for (const p of serie(n)) m.set(p.name, (m.get(p.name) ?? 0) + p.value)
        return [...m].map(([name, value]) => ({ name, value })).sort((a, b) => a.name.localeCompare(b.name))
    }
    const sel = [...new Set(funcionarios.map((f) => f.trim()).filter(Boolean))]
    if (sel.length === 1) return serie(sel[0])
    if (sel.length > 1) return soma(sel)
    const dia = objetos(producao?.recursal_resolvidos_por_dia_NG).map((p) => ({
        name: texto(p.name),
        value: n0(p.value),
    }))
    return dia.length > 0 ? dia : soma(Object.keys(porFunc))
}

// --- a resposta inteira ---

export type VisaoRecursal = 'por_prazo' | 'concluidas'
const KPIS: Record<
    VisaoRecursal,
    Record<'total' | 'emAndamento' | 'vencidas' | 'vencemHoje' | 'concluidas', string>
> = {
    por_prazo: {
        total: 'total_por_prazo_atividades_recursos_NG',
        emAndamento: 'por_prazo_em_andamento_atividades_recursos_NG',
        vencidas: 'por_prazo_vencidas_atividades_recursos_NG',
        vencemHoje: 'por_prazo_vencem_hoje_atividades_recursos_NG',
        concluidas: 'por_prazo_concluidas_atividades_recursos_NG',
    },
    concluidas: {
        total: 'total_atividades_recursos_NG',
        emAndamento: 'atividades_recursos_em_andamento_NG',
        vencidas: 'atividades_recursos_vencidas_NG',
        vencemHoje: 'atividades_recursos_vencem_hoje_NG',
        concluidas: 'atividades_recursos_concluidas_NG',
    },
}

export function lerRecursal(data: RecursalResponse) {
    const p = st(data.periodo)
    const d = st(data.decisoes)
    const c = st(data.controle)
    const unidade = data.unidade ?? 'NG'
    const base = (k: 'subfase' | 'materia' | 'competencia' | 'vara', b: Base) =>
        desc(linhas(data[k]?.[b]?.[`recursal_por_${k}_NG`]))
    const cancelA = numero(p.avr_retorno_recurso_cancelado_NG)
    const cancelB = numero(p.retorno_cr_recurso_cancelado_NG)
    const qtdProv = numero(p.provimento_mensal_qtd_NG)
    const metaProv = numero(p.provimento_mensal_meta_NG) ?? 80
    const comMerito = numero(c.controle_processo_extintos_com_merito_2g_qtd_recursal_NG)
    const semMerito = numero(c.controle_processo_extintos_sem_merito_2g_qtd_recursal_NG)
    const totalDec = n0(d.total_decisoes_recursal_NG)
    const kpis = (v: VisaoRecursal) =>
        Object.fromEntries(Object.entries(KPIS[v]).map(([k, campo]) => [k, numero(p[campo])])) as Record<
            keyof (typeof KPIS)['por_prazo'],
            number | null
        >
    return {
        unidade,
        temDados: data.periodo !== undefined,
        totalRecursal: numero(st(data.historico).total_recursal_NG),
        entrada: numero(p.entrada_recursal_NG),
        // v1: "Valor entrada acórdão Recursal" lia valor_causa_acordo_recursal_entrada_NG, que a rota nunca manda, e
        // caía neste: a soma do VALOR_CAUSA_ACORDO de todo o estoque da fase (sem período).
        valorAcordao: numero(p.valor_causa_acordo_recursal_NG),
        // LA: sem "Cancelados" e sem "Meta de provimento" (a rota do LA não manda os campos).
        cancelados: cancelA === null && cancelB === null ? null : (cancelA ?? 0) + (cancelB ?? 0),
        provimento:
            qtdProv === null
                ? null
                : { qtd: qtdProv, meta: metaProv, pct: metaProv > 0 ? (qtdProv / metaProv) * 100 : 0 },
        kpis: { por_prazo: kpis('por_prazo'), concluidas: kpis('concluidas') },
        porAtividade: desc(linhas(data.periodo?.recursal_processos_por_atividade_NG)),
        demandas: objetos(data.periodo?.recursal_demandas_por_funcionario_NG)
            .map((r): DemandaFuncionario => ({
                name: texto(r.name),
                cumpridas: n0(r.encerrado_cumprido),
                naoCumpridas: n0(r.encerrado_nao_cumprido),
                total: n0(r.encerrado_cumprido) + n0(r.encerrado_nao_cumprido),
            }))
            .sort((a, b) => b.total - a.total),
        media: linhas(data.periodo?.recursal_media_resolvidos_por_funcionario_NG).map((l) => ({
            name: l.name,
            value: l.value,
        })),
        lista: tarefas(data.periodo?.recursal_atividades_lista_NG) as Tarefa[],
        opcoesLista: opcoesLista(data.periodo?.recursal_atividades_lista_filtros_opcoes_NG) as OpcoesLista,
        distribuicao: (b: Base) => ({
            subfase: base('subfase', b),
            materia: base('materia', b),
            competencia: base('competencia', b),
            vara: base('vara', b),
            total:
                b === 'entrada'
                    ? (numero(st(data.subfase?.entrada).entrada_recursal_NG) ?? numero(p.entrada_recursal_NG))
                    : (numero(st(data.subfase?.estoque).total_recursal_NG) ??
                      numero(st(data.historico).total_recursal_NG)),
        }),
        decisoes: {
            total: totalDec,
            itens: DECISOES.map((x) => ({
                ...x,
                qtd: n0(d[`total_${x.key}_recurso_NG`]),
                pct: n0(d[`percent_${x.key}_recursal_NG`]),
            })),
        },
        status1g: desc(linhas(data.status_1g?.recursal_por_status_1g_NG, 'id_1g')),
        status2g: desc(linhas(data.status_2g?.recursal_por_status_2g_NG, 'id_2g')),
        juizes: ranking(data.juizes?.ranking_juizes_recursal_NG),
        relatores: ranking(data.relatores?.ranking_relatores_recursal_NG),
        extintos: {
            comMerito,
            valorComMerito: numero(c.controle_processo_extintos_com_merito_2g_valor_causa_acordao_recursal_NG),
            semMerito,
            valorSemMerito: numero(c.controle_processo_extintos_sem_merito_2g_valor_causa_acordao_recursal_NG),
            taxa: numero(c.controle_processo_taxa_provimento_2g_recursal_NG),
            total: (comMerito ?? 0) + (semMerito ?? 0),
            porTipo: porTipo(
                data.controle?.controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_recursal_NG,
            ),
            // NG e LA: do controle de processo, sem os filtros da página (como a v1); RJ: do próprio Recursal.
            seguemFiltros: unidade === 'RJ',
        },
        opcoes: {
            status1g: objetos(data.opcoes?.status_1g).map((o) => ({ value: texto(o.id), label: texto(o.label) })),
            status2g: objetos(data.opcoes?.status_2g).map((o) => ({ value: texto(o.id), label: texto(o.label) })),
            decisoes: objetos(data.opcoes?.decisoes).map((o) => ({ value: texto(o.id), label: texto(o.label) })),
            extintos: objetos(data.opcoes?.extintos_2g).map((o) => ({ value: texto(o.id), label: texto(o.label) })),
            juizes: textos(data.opcoes?.juizes),
            relatores: textos(data.opcoes?.relatores),
            materias: textos(data.opcoes?.materias),
            competencias: textos(data.opcoes?.competencias),
            varas: textos(data.opcoes?.varas),
            subfases: textos(data.opcoes?.subfases),
        },
    }
}

export type Recursal = ReturnType<typeof lerRecursal>

// --- Relatório de comissão do setor Recursos (só NG, como a v1: /recursal_NG/comissao/export) ---

const brl = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const inteiro = (v: number) => v.toLocaleString('pt-BR')
const dataBr = (iso: string) =>
    /^\d{4}-\d{2}-\d{2}/.test(iso) ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}` : iso || '—'

// A tabela da v1 (_gerar_pdf_export_comissao_recursos_ng): resumo por colaborador e, numa página nova, o
// detalhamento dos descontos por erro (para revisar antes de fechar a folha). Sem o bloco na resposta (LA, RJ ou
// sem permissão): sem comissão.
export function comissaoRecursal(data: RecursalResponse): CommissionTable | undefined {
    const c = obj(data.comissao)
    if (!Array.isArray(c.linhas)) return undefined
    const meta = n0(c.meta) || 80
    const qtd = n0(c.qtd_provimento)
    const erros = (n: number, desconto: number) => (n ? `${inteiro(n)} (-${brl(desconto)})` : '—')
    return {
        title: `Relatório de Comissão — Setor Recursos (${data.unidade ?? 'NG'})`,
        notes: [
            c.meta_atingida === true
                ? `Meta de qualidade: ATINGIDA (${inteiro(qtd)}/${inteiro(meta)} processos providos) — bônus de R$ 200,00 aplicado a todos`
                : `Meta de qualidade: não atingida (${inteiro(qtd)}/${inteiro(meta)} processos providos)`,
        ],
        columns: [
            { key: 'funcionario', label: 'Colaborador' },
            { key: 'subsetores', label: 'Subsetor' },
            { key: 'qtd_analise', label: 'Qtd. Análise', format: inteiro, sum: true },
            { key: 'valor_qtd_analise', label: 'Vlr. Análise', format: brl, sum: true },
            { key: 'qtd_confeccao', label: 'Qtd. Confecção', format: inteiro, sum: true },
            { key: 'valor_qtd_confeccao', label: 'Vlr. Confecção', format: brl, sum: true },
            { key: 'erros_analise', label: 'Erros / desconto Análise' },
            { key: 'erros_confeccao', label: 'Erros / desconto Confecção' },
            { key: 'bonus_meta_qualidade', label: 'Bônus meta', format: brl, sum: true },
            { key: 'bonus_zero_retrabalho', label: 'Bônus zero retrabalho', format: brl, sum: true },
            { key: 'valor_total', label: 'Total', format: brl, sum: true },
        ],
        rows: objetos(c.linhas).map((l) => ({
            funcionario: texto(l.funcionario),
            subsetores: textos(l.subsetores).join(' + '),
            qtd_analise: n0(l.qtd_analise),
            valor_qtd_analise: n0(l.valor_qtd_analise),
            qtd_confeccao: n0(l.qtd_confeccao),
            valor_qtd_confeccao: n0(l.valor_qtd_confeccao),
            erros_analise: erros(n0(l.erros_analise), n0(l.desconto_analise)),
            erros_confeccao: erros(n0(l.erros_confeccao), n0(l.desconto_confeccao)),
            bonus_meta_qualidade: n0(l.bonus_meta_qualidade),
            bonus_zero_retrabalho: n0(l.bonus_zero_retrabalho),
            valor_total: n0(l.valor_total),
        })),
        sortBy: 'valor_total',
        details: {
            title: 'Detalhamento dos descontos por erro',
            warning:
                'Revisar antes de fechar a folha: muitos casos (renúncia do cliente, ausência em audiência sem justificativa, trânsito em julgado, etc.) não são erro do colaborador — o sistema não distingue isso automaticamente com segurança.',
            columns: [
                { key: 'funcionario', label: 'Colaborador' },
                { key: 'subsetor', label: 'Subsetor' },
                { key: 'processo', label: 'Processo' },
                { key: 'atividade', label: 'Atividade de origem' },
                { key: 'data', label: 'Data' },
                { key: 'tipo', label: 'Tipo' },
                { key: 'desconto', label: 'Desconto' },
                { key: 'motivo', label: 'Motivo (texto do fechamento do retorno)' },
            ],
            rows: objetos(c.detalhes).map((d) => ({
                funcionario: texto(d.funcionario),
                subsetor: texto(d.subsetor),
                processo: texto(d.numero_processo) || '—',
                atividade: texto(d.atividade_origem),
                data: dataBr(texto(d.data)),
                tipo: texto(d.tipo_desconto),
                desconto: `-${brl(n0(d.valor_desconto))}`,
                motivo: texto(d.motivo_texto),
            })),
        },
    }
}
