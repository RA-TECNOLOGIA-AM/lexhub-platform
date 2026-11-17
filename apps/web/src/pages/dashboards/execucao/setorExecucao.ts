import type { FilterField } from '../../../lib/filters.ts'
import type { Tone } from '../../../components/dashboard/tone.ts'
import { normalizar, type PontoComarca } from '../../../lib/mapa.ts'
import type { DashboardFilters, Point } from '../../../types/index.ts'

// O que as páginas NG da v1 de Execução Condenação (NG/Execucao.tsx) e Execução Acordos (NG/ExecucaoAcordos.tsx)
// têm em comum: as seções "Atividades" (agendamentos do setor, nas visões Concluídas e Por prazo) e
// "Diligências", e o modal de atrasos. Os nomes dos campos seguem o prefixo da rota (execucao_..._NG ou
// execucao_acordos_..._NG); os de `stats` das atividades não seguem um padrão só, por isso vêm de CAMPOS.
// Só lógica pura (testada em setorExecucao.test.ts).

export type Setor = 'condenacao' | 'acordos'
export type VisaoAtividades = 'concluidas' | 'por_prazo'

// Uma linha de "Demandas por funcionário" (v1: RecursalDemandasFuncionarioRow).
export type DemandaFuncionario = { name: string; total: number; cumpridas: number; naoCumpridas: number }

// Uma tarefa da lista de atividades (v1: RecursalAtividadeTarefaRow).
export type Tarefa = {
    id: string
    descricao: string
    status: string
    responsavel: string
    encerradoPor: string | null // quem encerrou, quando não foi o responsável
    setor: string
    atividade: string
    processo: string | null
    criadoEm: string | null
    prazo: string | null
    valor: number | null
    vencida: boolean
    venceHoje: boolean
    concluida: boolean
}

export type OpcoesLista = {
    funcionarios: string[]
    atividades: string[]
    status: string[]
    situacoes: { id: string; label: string }[]
}

export type Atividades = {
    total: number | null
    emAndamento: number | null
    vencidas: number | null
    vencemHoje: number | null
    concluidas: number | null
    porAtividade: Point[]
    porFuncionario: DemandaFuncionario[]
    mediaPorFuncionario: Point[]
    resolvidosPorDia: Point[] // histórico todo (name = '2026-11-03')
    lista: Tarefa[]
    opcoes: OpcoesLista
}

// Um processo da lista "Valor Realizado (Alvará)" e das listas de execuções (v1: ExecucaoAcordosListaRow).
export type ProcessoLista = {
    processo: string
    uf: string
    subfase: string
    dataExecucao: string | null
    valor: number | null
}

export type Diligencias = {
    total: number | null
    alvaras: number | null // diligências de expedição de alvará
    alvarasCumpridos: number | null
    valorRealizado: number | null
    porProcesso: { processo: string; valor: number | null; quantidade: number }[]
    porColaborador: Point[]
    processosAlvara: ProcessoLista[]
}

export type Atraso = { dias: number; label: string; descricao: string; quantidade: number; pct: number }

export type SetorExecucao = {
    atividades: Record<VisaoAtividades, Atividades>
    diligencias: Diligencias
    atrasos: { total: number; faixas: Atraso[] }
}

// Os números de `stats` das atividades, por setor e visão (os nomes da v1).
const CAMPOS: Record<
    Setor,
    Record<VisaoAtividades, Record<'total' | 'emAndamento' | 'vencidas' | 'vencemHoje' | 'concluidas', string>>
> = {
    condenacao: {
        concluidas: {
            total: 'total_atividades_execucao_NG',
            emAndamento: 'atividades_execucao_em_andamento_NG',
            vencidas: 'atividades_execucao_vencidas_NG',
            vencemHoje: 'atividades_execucao_vencem_hoje_NG',
            concluidas: 'atividades_execucao_concluidas_NG',
        },
        por_prazo: {
            total: 'total_por_prazo_execucao_NG',
            emAndamento: 'por_prazo_em_andamento_execucao_NG',
            vencidas: 'por_prazo_vencidas_execucao_NG',
            vencemHoje: 'por_prazo_vencem_hoje_execucao_NG',
            concluidas: 'por_prazo_concluidas_execucao_NG',
        },
    },
    acordos: {
        concluidas: {
            total: 'total_atividades_execucao_acordos_NG',
            emAndamento: 'atividades_execucao_em_andamento_acordos_NG',
            vencidas: 'atividades_execucao_vencidas_acordos_NG',
            vencemHoje: 'atividades_execucao_vencem_hoje_acordos_NG',
            concluidas: 'atividades_execucao_concluidas_acordos_NG',
        },
        por_prazo: {
            total: 'total_por_prazo_execucao_acordos_NG',
            emAndamento: 'por_prazo_em_andamento_execucao_acordos_NG',
            vencidas: 'por_prazo_vencidas_execucao_acordos_NG',
            vencemHoje: 'por_prazo_vencem_hoje_execucao_acordos_NG',
            concluidas: 'por_prazo_concluidas_execucao_acordos_NG',
        },
    },
}

// O prefixo das listas da rota: execucao_processos_por_atividade_NG / execucao_acordos_processos_por_atividade_NG.
const PREFIXO: Record<Setor, string> = { condenacao: 'execucao', acordos: 'execucao_acordos' }

// --- leitura solta (a resposta da v1 pode faltar qualquer campo: vira null/[]) ---

export const numero = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)

const texto = (v: unknown): string => (v === null || v === undefined ? '' : String(v).trim())

const objetos = (v: unknown): Record<string, unknown>[] =>
    Array.isArray(v) ? v.filter((x): x is Record<string, unknown> => typeof x === 'object' && x !== null) : []

export function pontos(v: unknown): Point[] {
    return objetos(v).map((p) => ({ name: texto(p.name), value: numero(p.value) ?? 0 }))
}

// Comarcas da v1 (ChartDataPoint com `uf` e `tempo_medio_dias`): o que o mapa usa.
export type Comarcas = { quantidade: PontoComarca[]; valor: { name: string; value: number; uf: string }[] }

export function comarcas(quantidade: unknown, valor: unknown): Comarcas {
    return {
        quantidade: objetos(quantidade).map((p) => ({
            name: texto(p.name),
            value: numero(p.value) ?? 0,
            uf: texto(p.uf),
            tempoMedio: numero(p.tempo_medio_dias),
        })),
        valor: objetos(valor).map((p) => ({ name: texto(p.name), value: numero(p.value) ?? 0, uf: texto(p.uf) })),
    }
}

const textos = (v: unknown): string[] => (Array.isArray(v) ? v.map(texto).filter(Boolean) : [])

// '00012345620248040001' -> '0001234-56.2024.8.04.0001' (o nº CNJ, como a v1 mostra). Outro formato fica igual.
export function numeroCnj(raw: string | null | undefined): string {
    if (!raw) return '—'
    const d = raw.replace(/\D/g, '')
    if (d.length !== 20) return raw
    return `${d.slice(0, 7)}-${d.slice(7, 9)}.${d.slice(9, 13)}.${d.slice(13, 14)}.${d.slice(14, 16)}.${d.slice(16, 20)}`
}

function tarefas(v: unknown): Tarefa[] {
    return objetos(v).map((r, i) => {
        const responsavel = texto(r.funcionario_atribuido) || texto(r.funcionario)
        const encerrou = texto(r.funcionario_encerramento)
        return {
            id: texto(r.id) || String(i),
            descricao: texto(r.descricao),
            status: texto(r.status),
            responsavel,
            encerradoPor: r.encerrado_pelo_responsavel === false && encerrou ? encerrou : null,
            setor: texto(r.pessoa_setor),
            atividade: texto(r.atividade),
            processo: texto(r.numero_processo) || null,
            criadoEm: texto(r.criado_em) || null,
            prazo: texto(r.prazo) || null,
            valor: numero(r.valor_execucao),
            vencida: r.vencida === true,
            venceHoje: r.vence_hoje === true,
            concluida: r.concluida === true,
        }
    })
}

function opcoesLista(v: unknown): OpcoesLista {
    const o = typeof v === 'object' && v !== null ? (v as Record<string, unknown>) : {}
    return {
        funcionarios: textos(o.funcionarios),
        atividades: textos(o.atividades),
        status: textos(o.status),
        situacoes: objetos(o.situacoes)
            .map((s) => ({ id: texto(s.id), label: texto(s.label) || texto(s.id) }))
            .filter((s) => s.id),
    }
}

export function processosLista(v: unknown): ProcessoLista[] {
    return objetos(v).map((r) => ({
        processo: texto(r.numero_processo),
        uf: texto(r.uf),
        subfase: texto(r.subfase),
        dataExecucao: texto(r.data_execucao) || null,
        valor: numero(r.valor_execucao),
    }))
}

// O prefixo da rota da resposta (as duas páginas leem as mesmas partes com nomes diferentes).
export function lerSetor(data: Record<string, unknown>, setor: Setor): SetorExecucao {
    const s = (typeof data.stats === 'object' && data.stats !== null ? data.stats : {}) as Record<string, unknown>
    const p = PREFIXO[setor]
    const lista = (nome: string) => data[`${p}_${nome}_NG`]

    const visao = (v: VisaoAtividades): Atividades => {
        const c = CAMPOS[setor][v]
        const sufixo = v === 'por_prazo' ? '_por_prazo' : ''
        return {
            total: numero(s[c.total]),
            emAndamento: numero(s[c.emAndamento]),
            vencidas: numero(s[c.vencidas]),
            vencemHoje: numero(s[c.vencemHoje]),
            concluidas: numero(s[c.concluidas]),
            porAtividade: pontos(lista(`processos_por_atividade${sufixo}`)),
            porFuncionario: objetos(lista(`demandas_por_funcionario${sufixo}`)).map((r) => ({
                name: texto(r.name),
                total: numero(r.total) ?? 0,
                cumpridas: numero(r.encerrado_cumprido) ?? 0,
                naoCumpridas: numero(r.encerrado_nao_cumprido) ?? 0,
            })),
            mediaPorFuncionario: pontos(lista(`media_resolvidos_por_funcionario${sufixo}`)),
            resolvidosPorDia: pontos(lista(`resolvidos_por_dia${sufixo}`)),
            lista: tarefas(lista(`atividades_lista${sufixo}`)),
            opcoes: opcoesLista(lista(`atividades_lista_filtros_opcoes${sufixo}`)),
        }
    }

    const atrasos = typeof lista('atrasos_detalhamento') === 'object' ? lista('atrasos_detalhamento') : null
    const a = (atrasos ?? {}) as Record<string, unknown>

    const alvo = setor === 'acordos' ? 'execucao_acordos_NG' : 'execucao_NG'
    return {
        atividades: { concluidas: visao('concluidas'), por_prazo: visao('por_prazo') },
        diligencias: {
            total: numero(s[`total_diligencias_${alvo}`]),
            alvaras: numero(s[`total_diligencias_expedicao_alvara_${alvo}`]),
            alvarasCumpridos: numero(s[`cumpridas_diligencias_expedicao_alvara_${alvo}`]),
            valorRealizado: numero(s[`valor_diligencias_expedicao_alvara_${alvo}`]),
            porProcesso: objetos(lista('diligencias_por_processo')).map((r) => ({
                processo: texto(r.name),
                valor: numero(r.valor_execucao),
                quantidade: numero(r.value) ?? 0,
            })),
            porColaborador: objetos(lista('diligencias_por_funcionario')).map((r) => ({
                name: texto(r.name),
                value: numero(r.total) ?? 0,
            })),
            processosAlvara: processosLista(lista('diligencias_expedicao_alvara_processos')),
        },
        atrasos: {
            total: numero(a.total) ?? 0,
            faixas: objetos(a.buckets).map((b) => ({
                dias: numero(b.dias) ?? 0,
                label: texto(b.label),
                descricao: texto(b.descricao),
                quantidade: numero(b.count) ?? 0,
                pct: numero(b.pct) ?? 0,
            })),
        },
    }
}

// A produção diária da v1 ("mês a mês" com detalhe por dia): os dias somados por mês ('2026-11-03' -> 'nov 2026').
const MES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

export function diasPorMes(dias: Point[]): Point[] {
    const meses = new Map<string, number>()
    for (const d of dias) {
        const m = /^(\d{4})-(\d{2})-\d{2}/.exec(d.name)
        if (!m) continue
        const nome = `${MES[Number(m[2]) - 1]} ${m[1]}`
        meses.set(nome, (meses.get(nome) ?? 0) + d.value)
    }
    return [...meses.entries()].map(([name, value]) => ({ name, value }))
}

// Os dias de um mês ('2026-11'), em ordem.
export function diasDoMes(dias: Point[], mes: string): Point[] {
    return dias.filter((d) => d.name.startsWith(`${mes}-`)).sort((a, b) => a.name.localeCompare(b.name))
}

// Os meses que têm dia ('2026-11'), do mais recente para o mais antigo (o seletor "Detalhar mês").
export function mesesComDias(dias: Point[]): string[] {
    const meses = new Set(dias.map((d) => d.name.slice(0, 7)).filter((m) => /^\d{4}-\d{2}$/.test(m)))
    return [...meses].sort().reverse()
}

// --- filtros das seções (os parâmetros da rota da v1; vão na URL, mas ficam na própria seção) ---

export type ChavesSetor = Record<
    'funcionario' | 'atividade' | 'situacao' | 'status' | 'tipoDiligencia' | 'colaborador',
    keyof DashboardFilters
>

export const CHAVES: Record<Setor, ChavesSetor> = {
    condenacao: {
        funcionario: 'funcionario_execucao',
        atividade: 'atividade_execucao',
        situacao: 'situacao_execucao',
        status: 'status_execucao',
        tipoDiligencia: 'diligencia_tipo_execucao',
        colaborador: 'diligencia_colaborador_execucao',
    },
    acordos: {
        funcionario: 'funcionario_execucao_acordos',
        atividade: 'atividade_execucao_acordos',
        situacao: 'situacao_execucao_acordos',
        status: 'status_execucao_acordos',
        tipoDiligencia: 'diligencia_tipo_execucao_acordos',
        colaborador: 'diligencia_colaborador_execucao_acordos',
    },
}

// Os dois tipos do filtro de diligência da v1 (os cards clicáveis da seção Diligências).
export const TIPOS_DILIGENCIA = [
    { value: 'expedicao_alvara', label: 'Expedição de alvará' },
    { value: 'expedicao_alvara_cumprida', label: 'Alvará cumprido' },
]

const SITUACOES_PADRAO = [
    { id: 'em_andamento', label: 'Em andamento' },
    { id: 'vencidas', label: 'Vencidas' },
    { id: 'vencem_hoje', label: 'Vencem hoje' },
    { id: 'concluidas', label: 'Concluídas' },
]

const opcoes = (xs: string[]) =>
    [...new Set(xs.filter(Boolean))].sort((a, b) => a.localeCompare(b, 'pt-BR')).map((v) => ({ value: v, label: v }))

// Os seletores das seções Atividades e Diligências (inline: não entram na janela Filtros nem no "Limpar todos").
export function filtrosSetor(setor: Setor, s: SetorExecucao): FilterField[] {
    const k = CHAVES[setor]
    const visoes = [s.atividades.concluidas, s.atividades.por_prazo]
    const situacoes = visoes.find((v) => v.opcoes.situacoes.length > 0)?.opcoes.situacoes ?? SITUACOES_PADRAO
    return [
        {
            key: k.funcionario,
            label: 'Funcionário',
            options: opcoes(visoes.flatMap((v) => [...v.opcoes.funcionarios, ...v.porFuncionario.map((p) => p.name)])),
            inline: true,
        },
        {
            key: k.atividade,
            label: 'Atividade',
            options: opcoes(visoes.flatMap((v) => [...v.opcoes.atividades, ...v.porAtividade.map((p) => p.name)])),
            inline: true,
        },
        {
            key: k.situacao,
            label: 'Situação',
            options: situacoes.map((x) => ({ value: x.id, label: x.label })),
            inline: true,
        },
        { key: k.status, label: 'Status', options: opcoes(visoes.flatMap((v) => v.opcoes.status)), inline: true },
        { key: k.tipoDiligencia, label: 'Diligência', options: TIPOS_DILIGENCIA, single: true, inline: true },
        {
            key: k.colaborador,
            label: 'Colaborador',
            options: opcoes(s.diligencias.porColaborador.map((p) => p.name)),
            single: true,
            inline: true,
        },
    ]
}

// Os filtros da página (janela Filtros): UF, comarca, matéria e subfase, com as opções da base inteira.
export function filtrosPagina(o: {
    ufs: string[]
    comarcas: string[]
    materias: string[]
    subfases: string[]
}): FilterField[] {
    return [
        { key: 'uf', label: 'UF', options: opcoes(o.ufs) },
        { key: 'comarca', label: 'Comarca', options: opcoes(o.comarcas) },
        { key: 'materia', label: 'Matéria', options: opcoes(o.materias) },
        { key: 'subfase', label: 'Subfase', options: opcoes(o.subfases) },
    ]
}

// A cor do status da tarefa: Visualizado laranja, Cumprido verde, Não cumprido vermelho; os demais, neutros.
export function tomStatus(status: string): Tone {
    const s = normalizar(status)
    if (s.includes('NAO CUMPRIDO')) return 'danger'
    if (s.includes('CUMPRIDO')) return 'ok'
    if (s.includes('VISUALIZADO')) return 'accent'
    return 'neutral'
}
