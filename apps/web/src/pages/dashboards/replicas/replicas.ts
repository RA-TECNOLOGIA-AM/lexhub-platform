import type { CommissionTable } from '../../../lib/commissionReport.ts'
import type { FilterField } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters, Meta, Point } from '../../../types/index.ts'
import { opcoesLista, pontos, tarefas, type DemandaFuncionario } from '../execucao/setorExecucao.ts'
import { SITUACOES } from '../julgados-acordaos/filters.ts'
import type { Visao, VisaoDados } from '../pendencias-intermediarias/intermediarias.ts'

// Réplicas (LexFlow, NG, LA e RJ; o RJ com o cálculo do NG): as páginas da v1 NG/Replicas_NG.tsx e LA/Replicas_LA.tsx. A API
// (app/dashboards/replicas.py) junta as duas chamadas da página numa resposta só, com os nomes da NG.
// Só lógica pura (testada em replicas.test.ts).

export type ReplicasResponse = { meta: Meta; unidade?: string; stats?: Record<string, unknown> } & Record<
    string,
    unknown
>

export type Procedencia = {
    taxa: number | null
    procedentes: number | null
    decididos: number | null
    totalProcessos: number | null
    pendentes: number | null
}

export type Replicas = {
    unidade: 'NG' | 'LA' | 'RJ' // o RJ não tem a página na v1: usa o cálculo do NG (sem comissão)
    temDados: boolean
    visoes: Record<Visao, VisaoDados>
    procedencia: Procedencia
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

export function lerReplicas(data: ReplicasResponse): Replicas {
    const s = (data.stats ?? {}) as Record<string, unknown>
    const st = (k: string) => numero(s[k])
    const d = (k: string) => data[`${k}_NG`]
    const visao = (prazo: boolean): VisaoDados => {
        const pp = prazo ? '_por_prazo' : ''
        return {
            cards: prazo
                ? {
                      total: st('total_por_prazo_replicas_NG'),
                      emAndamento: st('por_prazo_em_andamento_replicas_NG'),
                      vencidas: st('por_prazo_vencidas_replicas_NG'),
                      vencemHoje: st('por_prazo_vencem_hoje_replicas_NG'),
                      concluidas: st('por_prazo_concluidas_replicas_NG'),
                  }
                : {
                      total: st('total_atividades_replicas_NG'),
                      emAndamento: st('atividades_replicas_em_andamento_NG'),
                      vencidas: st('atividades_replicas_vencidas_NG'),
                      vencemHoje: st('atividades_replicas_vencem_hoje_NG'),
                      concluidas: st('atividades_replicas_concluidas_NG'),
                  },
            porAtividade: pontos(d(`replicas_processos_por_atividade${pp}`)).sort(porValor),
            porFuncionario: demandas(d(`replicas_demandas_por_funcionario${pp}`)),
            lista: tarefas(d(prazo ? 'replicas_por_prazo_lista' : 'replicas_atividades_lista')),
            porDia: pontos(d(`replicas_concluidas${pp}_por_dia`)),
            porDiaPorFuncionario: porFuncionario(d(`replicas_concluidas${pp}_por_dia_por_funcionario`)),
            media: pontos(d(`media_replicas_concluidas${pp}_por_funcionario`)).sort(porValor),
        }
    }
    const opcoesConcluidas = opcoesLista(d('replicas_atividades_lista_filtros_opcoes'))
    const opcoesPrazo = opcoesLista(d('replicas_por_prazo_lista_filtros_opcoes'))
    return {
        unidade: data.unidade === 'LA' || data.unidade === 'RJ' ? data.unidade : 'NG',
        temDados: 'stats' in data && Object.values(s).some((v) => v !== null && v !== undefined),
        visoes: { concluidas: visao(false), por_prazo: visao(true) },
        procedencia: {
            taxa: st('replicas_taxa_procedencia_NG'),
            procedentes: st('replicas_procedencia_procedentes_NG'),
            decididos: st('replicas_procedencia_total_decididos_NG'),
            totalProcessos: st('replicas_procedencia_total_processos_NG'),
            pendentes: st('replicas_procedencia_pendentes_NG'),
        },
        funcionarios: unicos([...opcoesConcluidas.funcionarios, ...opcoesPrazo.funcionarios]),
        atividades: unicos([...opcoesConcluidas.atividades, ...opcoesPrazo.atividades]),
    }
}

// ---------- Comissão (só LA, como a v1; o NG não tem por decisão de 05/10/2026) ----------

// Valor por réplica concluída (VALOR_UNITARIO_PECA_REPLICAS_LA da v1).
export const VALOR_PECA_LA = 1.5

// O PDF da v1 (downloadComissionamentoReplicasLAPdf): Encerrado Cumprido com conclusão no período, por quem
// encerrou (as demandas por funcionário da visão Concluídas), × R$ 1,50.
export function comissaoReplicas(data: ReplicasResponse): CommissionTable | undefined {
    const r = lerReplicas(data)
    if (r.unidade !== 'LA') return undefined
    const linhas = r.visoes.concluidas.porFuncionario.filter((f) => f.cumpridas > 0)
    if (linhas.length === 0) return undefined
    return {
        title: 'Comissionamento — Réplicas LA',
        notes: [
            'Comissão por peça (réplica) concluída: R$ 1,50 — "Encerrado Cumprido" com data de conclusão no período',
        ],
        columns: [
            { key: 'funcionario', label: 'Funcionário' },
            { key: 'qtd_pecas', label: 'Qtd. peças', format: (v) => fmt.int(v), sum: true },
            { key: 'valor_unitario', label: 'Valor unit.', format: (v) => fmt.brl(v) },
            { key: 'valor_comissao', label: 'Comissão', format: (v) => fmt.brl(v), sum: true },
        ],
        rows: linhas
            .map((f) => ({
                funcionario: f.name,
                qtd_pecas: f.cumpridas,
                valor_unitario: VALOR_PECA_LA,
                valor_comissao: f.cumpridas * VALOR_PECA_LA,
            }))
            .sort((a, b) => a.funcionario.localeCompare(b.funcionario, 'pt-BR')),
        sortBy: 'valor_comissao',
    }
}

// ---------- Filtros ----------

const opcoes = (xs: string[], escolhidos: string[] = []) =>
    [...new Set([...xs, ...escolhidos])].map((v) => ({ value: v, label: v }))

// Funcionários e situação do processo, como a v1; a atividade vem do clique em "Por atividade" e aparece nas
// etiquetas (na v1 ela ficava sem etiqueta).
export function filtrosReplicas(data: ReplicasResponse, f: DashboardFilters = {}): FilterField[] {
    const r = lerReplicas(data)
    if (!r.temDados) return []
    return [
        { key: 'funcionario_replicas', label: 'Funcionários', options: opcoes(r.funcionarios, f.funcionario_replicas) },
        {
            key: 'atividade_replicas',
            label: 'Atividade',
            options: opcoes(r.atividades, f.atividade_replicas),
            fromChart: true,
        },
        { key: 'situacao_processo', label: 'Situação do processo', options: SITUACOES },
    ]
}
