import type { CommissionColumn, CommissionTable } from '../../../lib/commissionReport.ts'
import type { FilterField } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters, Meta, Point } from '../../../types/index.ts'
import { opcoesLista, pontos, tarefas, type DemandaFuncionario } from '../execucao/setorExecucao.ts'
import { SITUACOES } from '../julgados-acordaos/filters.ts'
import type { Visao, VisaoDados } from '../pendencias-intermediarias/intermediarias.ts'

// Emendas e Manifestações (LexFlow, NG, LA e RJ; o RJ com o cálculo do NG): as páginas da v1 NG/EmendasManifestacoes_NG.tsx e
// LA/EmendasManifestacoes_LA.tsx. NG: setor MANIFESTAÇÃO (com UF); LA: setor INTERMEDIÁRIAS. A API
// (app/dashboards/emendas_manifestacoes.py) junta as duas chamadas da página numa resposta só, com os nomes da NG.
// Só lógica pura (testada em emendas.test.ts).

export type EmendasResponse = { meta: Meta; unidade?: string; stats?: Record<string, unknown> } & Record<
    string,
    unknown
>

export type FaixaLA = 'faixa_1' | 'faixa_2'

// Uma linha da comissão (emendas_manifestacoes_comissionamento_por_funcionario da v1), já calculada pela API.
export type LinhaComissao = {
    funcionario: string
    agendaFinalizada: number
    agendaTotal: number
    agendaPercentual: number
    elegivel: boolean
    faixa: FaixaLA | null
    qtdManifestacao: number
    valorManifestacao: number
    qtdDilacao: number
    valorDilacao: number
    valorComissao: number
    porUf: { uf: string; manifestacao: number; dilacao: number }[] // só NG
}

export type Emendas = {
    unidade: 'NG' | 'LA' | 'RJ' // o RJ não tem a página na v1: usa o cálculo do NG
    regra: 'NG' | 'LA' // de quem são as regras (cores, comissão, UF): o RJ segue as do NG
    temDados: boolean
    visoes: Record<Visao, VisaoDados>
    comissao: LinhaComissao[]
    comparativo: { manifestacoes: number | null; dilacoes: number | null } // só NG
    ufs: string[] // só NG
    funcionarios: string[]
    atividades: string[]
}

const numero = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)
const n0 = (v: unknown) => numero(v) ?? 0
const texto = (v: unknown) => (typeof v === 'string' ? v.trim() : v == null ? '' : String(v).trim())
const objetos = (v: unknown): Record<string, unknown>[] =>
    Array.isArray(v) ? v.filter((x): x is Record<string, unknown> => typeof x === 'object' && x !== null) : []
const porValor = (a: Point, b: Point) => b.value - a.value
const unicos = (xs: string[]) => [...new Set(xs.filter(Boolean))].sort((a, b) => a.localeCompare(b, 'pt-BR'))

function demandas(v: unknown): DemandaFuncionario[] {
    return objetos(v)
        .map((r) => ({
            name: texto(r.name),
            total: n0(r.total),
            cumpridas: n0(r.encerrado_cumprido),
            naoCumpridas: n0(r.encerrado_nao_cumprido),
        }))
        .filter((r) => r.name)
        .sort((a, b) => b.total - a.total)
}

function porFuncionario(v: unknown): Record<string, Point[]> {
    if (typeof v !== 'object' || v === null || Array.isArray(v)) return {}
    return Object.fromEntries(Object.entries(v).map(([nome, serie]) => [nome, pontos(serie)]))
}

function linhasComissao(v: unknown): LinhaComissao[] {
    return objetos(v)
        .map((r) => ({
            funcionario: texto(r.funcionario),
            agendaFinalizada: n0(r.agenda_finalizada),
            agendaTotal: n0(r.agenda_total),
            agendaPercentual: n0(r.agenda_percentual),
            elegivel: r.elegivel === true,
            faixa: r.faixa === 'faixa_1' || r.faixa === 'faixa_2' ? (r.faixa as FaixaLA) : null,
            qtdManifestacao: n0(r.qtd_manifestacao),
            valorManifestacao: n0(r.valor_manifestacao),
            qtdDilacao: n0(r.qtd_dilacao),
            valorDilacao: n0(r.valor_dilacao),
            valorComissao: n0(r.valor_comissao),
            porUf: objetos(r.resolvidos_por_uf).map((u) => ({
                uf: texto(u.uf) || 'Sem UF',
                manifestacao: n0(u.qtd_manifestacao),
                dilacao: n0(u.qtd_dilacao),
            })),
        }))
        .filter((r) => r.funcionario)
}

export function lerEmendas(data: EmendasResponse): Emendas {
    const s = (data.stats ?? {}) as Record<string, unknown>
    const st = (k: string) => numero(s[k])
    const d = (k: string) => data[`${k}_NG`]
    const opcoesConcluidas = opcoesLista(d('emendas_manifestacoes_atividades_lista_filtros_opcoes'))
    const opcoesPrazo = opcoesLista(d('emendas_manifestacoes_por_prazo_lista_filtros_opcoes'))
    const visao = (prazo: boolean): VisaoDados => {
        const pp = prazo ? '_por_prazo' : ''
        return {
            cards: prazo
                ? {
                      total: st('total_por_prazo_emendas_manifestacoes_NG'),
                      emAndamento: st('por_prazo_em_andamento_emendas_manifestacoes_NG'),
                      vencidas: st('por_prazo_vencidas_emendas_manifestacoes_NG'),
                      vencemHoje: st('por_prazo_vencem_hoje_emendas_manifestacoes_NG'),
                      concluidas: st('por_prazo_concluidas_emendas_manifestacoes_NG'),
                  }
                : {
                      total: st('total_atividades_emendas_manifestacoes_NG'),
                      emAndamento: st('atividades_emendas_manifestacoes_em_andamento_NG'),
                      vencidas: st('atividades_emendas_manifestacoes_vencidas_NG'),
                      vencemHoje: st('atividades_emendas_manifestacoes_vencem_hoje_NG'),
                      concluidas: st('atividades_emendas_manifestacoes_concluidas_NG'),
                  },
            porAtividade: pontos(d(`emendas_manifestacoes_processos_por_atividade${pp}`)).sort(porValor),
            porFuncionario: demandas(d(`emendas_manifestacoes_demandas_por_funcionario${pp}`)),
            lista: tarefas(
                d(prazo ? 'emendas_manifestacoes_por_prazo_lista' : 'emendas_manifestacoes_atividades_lista'),
            ),
            porDia: pontos(d(`emendas_manifestacoes_concluidas${pp}_por_dia`)),
            porDiaPorFuncionario: porFuncionario(d(`emendas_manifestacoes_concluidas${pp}_por_dia_por_funcionario`)),
            media: pontos(d(`media_emendas_manifestacoes_concluidas${pp}_por_funcionario`)).sort(porValor),
        }
    }
    return {
        unidade: data.unidade === 'LA' || data.unidade === 'RJ' ? data.unidade : 'NG',
        regra: data.unidade === 'LA' ? 'LA' : 'NG',
        temDados: 'stats' in data && Object.values(s).some((v) => v !== null && v !== undefined),
        visoes: { concluidas: visao(false), por_prazo: visao(true) },
        comissao: linhasComissao(d('emendas_manifestacoes_comissionamento_por_funcionario')),
        comparativo: {
            manifestacoes: st('comparativo_qtd_manifestacoes_emendas_manifestacoes_NG'),
            dilacoes: st('comparativo_qtd_dilacoes_emendas_manifestacoes_NG'),
        },
        ufs: unicos(
            Array.isArray(s.emendas_manifestacoes_uf_opcoes_NG) ? s.emendas_manifestacoes_uf_opcoes_NG.map(texto) : [],
        ),
        funcionarios: unicos([...opcoesConcluidas.funcionarios, ...opcoesPrazo.funcionarios]),
        atividades: unicos([...opcoesConcluidas.atividades, ...opcoesPrazo.atividades]),
    }
}

// ---------- Agenda cumprida (o bloco que substitui a dilação) ----------

export type Agenda = {
    rotulo: string
    finalizada: number
    total: number
    percentual: number // 1 casa
    temDados: boolean
    manifestacoes: number
    dilacoes: number
    faixa: FaixaLA | null // LA: a faixa do conjunto (o PDF aplica a de cada um)
    elegivel: boolean
}

// O agregado da v1 (comissaoAgregada): soma de quem está na comissão (a API já aplicou o filtro de funcionário).
export function agendaAgregada(linhas: LinhaComissao[], funcionarios: string[]): Agenda {
    const finalizada = linhas.reduce((s, l) => s + l.agendaFinalizada, 0)
    const total = linhas.reduce((s, l) => s + l.agendaTotal, 0)
    const percentual = total ? Math.round((finalizada / total) * 1000) / 10 : 0
    return {
        rotulo:
            funcionarios.length === 1
                ? funcionarios[0]
                : funcionarios.length > 1
                  ? `${funcionarios.length} funcionários selecionados`
                  : 'Todos os funcionários',
        finalizada,
        total,
        percentual,
        temDados: total > 0,
        manifestacoes: linhas.reduce((s, l) => s + l.qtdManifestacao, 0),
        dilacoes: linhas.reduce((s, l) => s + l.qtdDilacao, 0),
        faixa: percentual >= 97 ? 'faixa_2' : percentual >= 85 ? 'faixa_1' : null,
        elegivel: total > 0 && percentual >= 85,
    }
}

// ---------- "Por atividade": o que gera comissão (verde) e o que não gera (laranja) ----------

// NG: por exclusão (só a análise não comissiona). LA: lista fechada (as manifestações e a dilação de prazo).
const NAO_COMISSIONAVEIS_NG = new Set(['ANÁLISE DE MANIFESTAÇÃO', 'ELABORAR MANIFESTAÇÃO'])
const COMISSIONAVEIS_LA = new Set([
    'EMENDA À INICIAL',
    'MANIFESTAÇÃO (5D)',
    'MANIFESTAÇÃO (10D)',
    'MANIFESTAÇÃO (15D)',
    'MANIFESTAÇÃO CUSTAS DE CITAÇÃO',
    'MANIFESTAÇÃO REMESSA 2 GRAU',
    'MAN HIPO RECURSO',
    'MAN HIPOSSUFICIÊNCIA',
    'MAN DESNECESSIDADE DE AUDIÊNCIA',
    'MAN INTERPOSIÇÃO AGRAVO',
    'PEDIDO DE CELERIDADE',
    'PEDIDO SUSTENTAÇÃO ORAL',
    'DILAÇÃO DE PRAZO',
])
export const COR_GERA = 'var(--ok-dot)'
export const COR_NAO_GERA = 'var(--warn-dot)'

export function geraComissao(atividade: string, unidade: 'NG' | 'LA'): boolean {
    const nome = atividade.trim().toUpperCase()
    return unidade === 'NG' ? !NAO_COMISSIONAVEIS_NG.has(nome) : COMISSIONAVEIS_LA.has(nome)
}

export function coresAtividades(pontos: Point[], unidade: 'NG' | 'LA'): Record<string, string> {
    return Object.fromEntries(pontos.map((p) => [p.name, geraComissao(p.name, unidade) ? COR_GERA : COR_NAO_GERA]))
}

// ---------- Comissão (PDF) ----------

const brl = (v: number) => fmt.brl(v)
const inteiro = (v: number) => fmt.int(v)
const pct1 = (v: number) => `${fmt.dec1(v)}%`
export const ROTULO_FAIXA: Record<FaixaLA, string> = { faixa_1: 'Faixa 1', faixa_2: 'Faixa 2' }

// O PDF de comissionamento da v1 (downloadComissionamentoEmendasManifestacoes*Pdf), com as linhas que a API calcula.
// NG: valor fixo e as peças por UF; LA: a faixa de cada um pela agenda cumprida.
export function comissaoEmendas(data: EmendasResponse): CommissionTable | undefined {
    const e = lerEmendas(data)
    if (e.comissao.length === 0) return undefined
    const ordem = [...e.comissao].sort(
        (a, b) => b.valorComissao - a.valorComissao || a.funcionario.localeCompare(b.funcionario, 'pt-BR'),
    )
    if (e.regra === 'NG') {
        const ufs = [...new Set(e.comissao.flatMap((l) => l.porUf.map((u) => u.uf)))].sort((a, b) =>
            a === 'Sem UF' ? 1 : b === 'Sem UF' ? -1 : a.localeCompare(b, 'pt-BR'),
        )
        const colunasUf = (tipo: 'manifestacao' | 'dilacao'): CommissionColumn[] =>
            ufs.map((uf) => ({
                key: `${tipo}_${uf}`,
                label: `${tipo === 'manifestacao' ? 'Manif.' : 'Dil.'} ${uf}`,
                format: inteiro,
                sum: true,
            }))
        return {
            title: `Comissionamento — Emendas e Manifestações ${e.unidade}`,
            notes: [
                'Manifestação: R$ 1,00 por peça (Encerrado Cumprido, valor fixo) · Dilação: R$ 0,50 por peça (Encerrado Cumprido, valor fixo)',
                'Peças com prazo no período. A agenda cumprida é informativa (o NG não tem faixa).',
                ...(e.unidade === 'RJ'
                    ? ['No RJ, “Manifestar dilação de prazo” também conta como dilação (R$ 0,50).']
                    : []),
            ],
            columns: [
                { key: 'funcionario', label: 'Funcionário' },
                { key: 'agenda', label: 'Agenda cumprida', format: pct1 },
                ...colunasUf('manifestacao'),
                { key: 'qtd_manifestacao', label: 'Qtd. manifestação', format: inteiro, sum: true },
                { key: 'valor_manifestacao', label: 'Valor unit.', format: brl },
                ...colunasUf('dilacao'),
                { key: 'qtd_dilacao', label: 'Qtd. dilação', format: inteiro, sum: true },
                { key: 'valor_dilacao', label: 'Valor unit.', format: brl },
                { key: 'valor_comissao', label: 'Comissão', format: brl, sum: true },
            ],
            rows: ordem.map((l) => ({
                funcionario: l.funcionario,
                agenda: l.agendaPercentual,
                ...Object.fromEntries(
                    ufs.flatMap((uf) => {
                        const u = l.porUf.find((x) => x.uf === uf)
                        return [
                            [`manifestacao_${uf}`, u?.manifestacao ?? 0],
                            [`dilacao_${uf}`, u?.dilacao ?? 0],
                        ]
                    }),
                ),
                qtd_manifestacao: l.qtdManifestacao,
                valor_manifestacao: l.valorManifestacao,
                qtd_dilacao: l.qtdDilacao,
                valor_dilacao: l.valorDilacao,
                valor_comissao: l.valorComissao,
            })),
            sortBy: 'valor_comissao',
        }
    }
    return {
        title: 'Comissionamento — Emendas e Manifestações LA',
        notes: [
            'Abaixo de 85% da agenda finalizada: não elegível · Faixa 1 (85% a 96,9%): R$ 1,00 por Manifestação e R$ 0,25 por Dilação · Faixa 2 (a partir de 97%): R$ 1,50 por Manifestação e R$ 0,50 por Dilação',
            'A faixa é aplicada individualmente, conforme o percentual de agenda (agendamentos com prazo no período) finalizada por cada funcionário.',
        ],
        columns: [
            { key: 'funcionario', label: 'Funcionário' },
            { key: 'agenda', label: 'Agenda cumprida', format: pct1 },
            { key: 'faixa', label: 'Faixa' },
            { key: 'qtd_manifestacao', label: 'Qtd. manifestação', format: inteiro, sum: true },
            { key: 'valor_manifestacao', label: 'Valor unit. manif.', format: brl },
            { key: 'qtd_dilacao', label: 'Qtd. dilação', format: inteiro, sum: true },
            { key: 'valor_dilacao', label: 'Valor unit. dil.', format: brl },
            { key: 'valor_comissao', label: 'Comissão', format: brl, sum: true },
        ],
        rows: ordem.map((l) => ({
            funcionario: l.funcionario,
            agenda: l.agendaPercentual,
            faixa: !l.elegivel ? 'Não elegível' : l.faixa ? ROTULO_FAIXA[l.faixa] : '—',
            qtd_manifestacao: l.qtdManifestacao,
            valor_manifestacao: l.valorManifestacao,
            qtd_dilacao: l.qtdDilacao,
            valor_dilacao: l.valorDilacao,
            valor_comissao: l.valorComissao,
        })),
        sortBy: 'valor_comissao',
    }
}

// ---------- Filtros ----------

const opcoes = (xs: string[], escolhidos: string[] = []) =>
    [...new Set([...xs, ...escolhidos])].map((v) => ({ value: v, label: v }))

// Funcionários, UF (só NG) e situação do processo, como a v1; a atividade vem do clique em "Por atividade" e
// aparece nas etiquetas (na v1 do LA ela ficava sem etiqueta).
export function filtrosEmendas(data: EmendasResponse, f: DashboardFilters = {}): FilterField[] {
    const e = lerEmendas(data)
    if (!e.temDados) return []
    return [
        {
            key: 'funcionario_emendas_manifestacoes',
            label: 'Funcionários',
            options: opcoes(e.funcionarios, f.funcionario_emendas_manifestacoes),
        },
        ...(e.regra === 'NG'
            ? [
                  {
                      key: 'uf_emendas_manifestacoes' as const,
                      label: 'UF',
                      options: opcoes(e.ufs, f.uf_emendas_manifestacoes),
                  },
              ]
            : []),
        {
            key: 'atividade_emendas_manifestacoes',
            label: 'Atividade',
            options: opcoes(e.atividades, f.atividade_emendas_manifestacoes),
            fromChart: true,
        },
        { key: 'situacao_processo', label: 'Situação do processo', options: SITUACOES },
    ]
}
