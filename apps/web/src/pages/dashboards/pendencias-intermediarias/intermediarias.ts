import type { CommissionTable } from '../../../lib/commissionReport.ts'
import type { FilterField } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters, Meta, Point } from '../../../types/index.ts'
import { opcoesLista, pontos, tarefas, type DemandaFuncionario, type Tarefa } from '../execucao/setorExecucao.ts'
import { SITUACOES } from '../julgados-acordaos/filters.ts'

// Pendências Intermediárias (LexFlow, NG, LA e RJ; o RJ com o cálculo do NG): as páginas da v1 NG/PendenciasIntermediarias_NG.tsx e
// LA/PendenciasIntermediarias_LA.tsx. A API (app/dashboards/pendencias_intermediarias.py) junta as duas chamadas da
// página (período com filtros + histórico sem datas) numa resposta só, sempre com os nomes da NG.
// Só lógica pura (testada em intermediarias.test.ts).

export type PendenciasIntermediariasResponse = {
    meta: Meta
    unidade?: string
    stats?: Record<string, unknown>
} & Record<string, unknown>

export type Visao = 'por_prazo' | 'concluidas'

export type Cards = {
    total: number | null
    emAndamento: number | null
    vencidas: number | null
    vencemHoje: number | null
    concluidas: number | null
}

export type Faixa = 'ouro' | 'prata' | 'bronze'

export type Dilacao = {
    count: number | null
    totalEncerrados: number | null
    taxa: number | null
    faixa: Faixa | null
}

export type DilacaoFuncionario = {
    funcionario: string
    qtdDilacoes: number
    totalEncerrados: number
    qtdResolvidos: number
    taxa: number
}

export type VisaoDados = {
    cards: Cards
    porAtividade: Point[]
    porFuncionario: DemandaFuncionario[]
    lista: Tarefa[]
    // Histórico todo (sem datas): concluídas por dia, por dia de cada funcionário, e a média por funcionário.
    porDia: Point[]
    porDiaPorFuncionario: Record<string, Point[]>
    media: Point[]
}

export type Intermediarias = {
    unidade: 'NG' | 'LA' | 'RJ' // o RJ não tem a página na v1: usa o cálculo do NG
    temDados: boolean
    visoes: Record<Visao, VisaoDados>
    dilacao: Dilacao
    dilacoesPorFuncionario: DilacaoFuncionario[]
    funcionarios: string[] // opções do filtro (as das duas listas, sem repetir)
    atividades: string[]
}

const numero = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)
const n0 = (v: unknown) => numero(v) ?? 0
const texto = (v: unknown) => (typeof v === 'string' ? v.trim() : v == null ? '' : String(v).trim())
const objetos = (v: unknown): Record<string, unknown>[] =>
    Array.isArray(v) ? v.filter((x): x is Record<string, unknown> => typeof x === 'object' && x !== null) : []
const porValor = (a: Point, b: Point) => b.value - a.value

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

const FAIXAS: readonly string[] = ['ouro', 'prata', 'bronze']

export function lerIntermediarias(data: PendenciasIntermediariasResponse): Intermediarias {
    const s = (data.stats ?? {}) as Record<string, unknown>
    const st = (k: string) => numero(s[`${k}_NG`])
    const d = (k: string) => data[`${k}_NG`]
    const opcoesConcluidas = opcoesLista(d('intermediarias_atividades_lista_filtros_opcoes'))
    const opcoesPrazo = opcoesLista(d('intermediarias_por_prazo_lista_filtros_opcoes'))
    const unicos = (xs: string[]) => [...new Set(xs.filter(Boolean))].sort((a, b) => a.localeCompare(b, 'pt-BR'))
    const faixa = texto(s.dilacoes_intermediarias_faixa_NG)

    return {
        unidade: data.unidade === 'LA' || data.unidade === 'RJ' ? data.unidade : 'NG',
        temDados: 'stats' in data && Object.values(s).some((v) => v !== null && v !== undefined),
        visoes: {
            concluidas: {
                cards: {
                    total: st('total_atividades_intermediarias'),
                    emAndamento: st('atividades_intermediarias_em_andamento'),
                    vencidas: st('atividades_intermediarias_vencidas'),
                    vencemHoje: st('atividades_intermediarias_vencem_hoje'),
                    concluidas: st('atividades_intermediarias_concluidas'),
                },
                porAtividade: pontos(d('intermediarias_processos_por_atividade')).sort(porValor),
                porFuncionario: demandas(d('intermediarias_demandas_por_funcionario')),
                lista: tarefas(d('intermediarias_atividades_lista')),
                porDia: pontos(d('intermediarias_concluidas_por_dia')),
                porDiaPorFuncionario: porFuncionario(d('intermediarias_concluidas_por_dia_por_funcionario')),
                media: pontos(d('media_intermediarias_concluidas_por_funcionario')).sort(porValor),
            },
            por_prazo: {
                cards: {
                    total: st('total_por_prazo_intermediarias'),
                    emAndamento: st('por_prazo_em_andamento_intermediarias'),
                    vencidas: st('por_prazo_vencidas_intermediarias'),
                    vencemHoje: st('por_prazo_vencem_hoje_intermediarias'),
                    concluidas: st('por_prazo_concluidas_intermediarias'),
                },
                porAtividade: pontos(d('intermediarias_processos_por_atividade_por_prazo')).sort(porValor),
                porFuncionario: demandas(d('intermediarias_demandas_por_funcionario_por_prazo')),
                lista: tarefas(d('intermediarias_por_prazo_lista')),
                porDia: pontos(d('intermediarias_concluidas_por_prazo_por_dia')),
                porDiaPorFuncionario: porFuncionario(d('intermediarias_concluidas_por_prazo_por_dia_por_funcionario')),
                media: pontos(d('media_intermediarias_concluidas_por_prazo_por_funcionario')).sort(porValor),
            },
        },
        dilacao: {
            count: st('dilacoes_intermediarias_count'),
            totalEncerrados: st('dilacoes_intermediarias_total_encerrados'),
            taxa: st('dilacoes_intermediarias_taxa'),
            faixa: FAIXAS.includes(faixa) ? (faixa as Faixa) : null,
        },
        dilacoesPorFuncionario: objetos(d('dilacoes_intermediarias_por_funcionario'))
            .map((r) => ({
                funcionario: texto(r.funcionario),
                qtdDilacoes: n0(r.qtd_dilacoes),
                totalEncerrados: n0(r.total_encerrados),
                qtdResolvidos: n0(r.qtd_resolvidos),
                taxa: n0(r.taxa_dilacao),
            }))
            .filter((r) => r.funcionario),
        funcionarios: unicos([...opcoesConcluidas.funcionarios, ...opcoesPrazo.funcionarios]),
        atividades: unicos([...opcoesConcluidas.atividades, ...opcoesPrazo.atividades]),
    }
}

// A produção do histórico só dos funcionários escolhidos: soma as séries diárias deles (a v1 fazia isso no
// navegador, porque a chamada sem datas não recebe o filtro). Sem escolha, a série do setor inteiro.
export function diasDosFuncionarios(v: VisaoDados, funcionarios: string[]): Point[] {
    if (funcionarios.length === 0) return v.porDia
    const soma = new Map<string, number>()
    for (const nome of funcionarios) {
        for (const p of v.porDiaPorFuncionario[nome] ?? []) soma.set(p.name, (soma.get(p.name) ?? 0) + p.value)
    }
    return [...soma.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([name, value]) => ({ name, value }))
}

// ---------- Dilação e comissão (iguais na NG e no LA) ----------

// A faixa individual da v1 (faixaDilacaoIndividual): até 5% Ouro, até 10% Prata, até 15% Bronze; acima, ou sem
// encerrados, nenhuma.
export function faixaIndividual(taxa: number, totalEncerrados: number): Faixa | null {
    if (totalEncerrados <= 0 || taxa > 15) return null
    if (taxa <= 5) return 'ouro'
    if (taxa <= 10) return 'prata'
    return 'bronze'
}

// Valor por pendência resolvida em cada faixa (faixaComissaoUnitariaPendenciasIntermediarias* da v1).
export const VALOR_FAIXA: Record<Faixa, number> = { bronze: 0.5, prata: 1, ouro: 2 }

export const ROTULO_FAIXA: Record<Faixa, string> = { ouro: 'Ouro', prata: 'Prata', bronze: 'Bronze' }

const brl = (v: number) => fmt.brl(v)
const inteiro = (v: number) => fmt.int(v)
const pct1 = (v: number) => `${fmt.dec1(v)}%`

// O PDF de comissionamento da v1 (downloadComissionamentoPendenciasIntermediarias*Pdf): quem resolveu alguma
// pendência no período, com a faixa da própria taxa de dilação. Sem ninguém, o botão não aparece.
export function comissaoIntermediarias(data: PendenciasIntermediariasResponse): CommissionTable | undefined {
    const p = lerIntermediarias(data)
    const linhas = p.dilacoesPorFuncionario
        .filter((d) => d.qtdResolvidos > 0)
        .map((d) => {
            const faixa = faixaIndividual(d.taxa, d.totalEncerrados)
            const unitario = faixa ? VALOR_FAIXA[faixa] : 0
            return {
                funcionario: d.funcionario,
                qtd_resolvidos: d.qtdResolvidos,
                qtd_dilacoes: d.qtdDilacoes,
                taxa_dilacao: d.taxa,
                comissao_unitaria: unitario,
                valor_comissao: d.qtdResolvidos * unitario,
            }
        })
    if (linhas.length === 0) return undefined
    const taxaSetor = p.dilacao.taxa
    return {
        title: `Comissionamento — Pendências Intermediárias ${p.unidade}`,
        notes: [
            'Comissão por pendência resolvida: R$ 0,50 (Faixa Bronze — dilação de 10,1% a 15%) · R$ 1,00 (Faixa Prata — de 5,1% a 10%) · R$ 2,00 (Faixa Ouro — até 5%)',
            'A faixa é aplicada individualmente, conforme a taxa de dilação de cada funcionário no período.',
            ...(taxaSetor !== null ? [`Taxa de dilação do setor no período (informativo): ${pct1(taxaSetor)}`] : []),
        ],
        columns: [
            { key: 'funcionario', label: 'Funcionário' },
            { key: 'qtd_resolvidos', label: 'Qtd. resolvidos', format: inteiro, sum: true },
            { key: 'qtd_dilacoes', label: 'Qtd. dilações', format: inteiro, sum: true },
            { key: 'taxa_dilacao', label: 'Taxa de dilação atingida', format: pct1 },
            { key: 'comissao_unitaria', label: 'Valor', format: brl },
            { key: 'valor_comissao', label: 'Comissão', format: brl, sum: true },
        ],
        rows: linhas.sort((a, b) => a.funcionario.localeCompare(b.funcionario, 'pt-BR')),
        sortBy: 'valor_comissao',
    }
}

// ---------- Filtros ----------

const opcoes = (xs: string[], escolhidos: string[] = []) =>
    [...new Set([...xs, ...escolhidos])].map((v) => ({ value: v, label: v }))

// Os filtros da v1 (funcionários e situação do processo) e a atividade, que na v1 só se ligava clicando no
// gráfico "Por atividade" e ficava sem etiqueta; aqui ela aparece nas etiquetas e no "Limpar todos".
export function filtrosIntermediarias(data: PendenciasIntermediariasResponse, f: DashboardFilters = {}): FilterField[] {
    const p = lerIntermediarias(data)
    if (!p.temDados) return []
    return [
        {
            key: 'funcionario_intermediarias',
            label: 'Funcionários',
            options: opcoes(p.funcionarios, f.funcionario_intermediarias),
        },
        {
            key: 'atividade_intermediarias',
            label: 'Atividade',
            options: opcoes(p.atividades, f.atividade_intermediarias),
            fromChart: true,
        },
        { key: 'situacao_processo', label: 'Situação do processo', options: SITUACOES },
    ]
}
