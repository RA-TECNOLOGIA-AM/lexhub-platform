import type { Meta, Point } from '../../../types/index.ts'
import { MESES } from '../setor/datas.ts'

// Estratégico (área Estratégico): a página da v1 GERAL/Estrategico.tsx, por unidade. A API devolve as somas prontas
// (Comercial e Protocolo dos bancos legados + LexPre e o Jurídico do LexFlow; app/dashboards/estrategico.py); aqui
// ficam só as contas que a página da v1 fazia ao desenhar (comparativos, ticket médio por mês, dias de um mês).
// Só lógica pura (testada em estrategico.test.ts).

export type Subfase = {
    name: string
    value: number
    percent?: number
    valor_causa?: number
    valor_sentenca?: number
    valor_execucao?: number
    tempo_medio_dias?: number
}

// Processos por comarca (V2: com a UF mais comum e o valor de causa da comarca, para o mapa).
export type ComarcaPonto = Point & { percent?: number; uf?: string | null; valor_causa?: number }

export type Juridico = {
    fase_inicial_total_processos: number | null
    fase_inicial_valor_causa_total: number | null
    fase_recursal_total_processos: number | null
    fase_recursal_valor_causa_total: number | null
    fase_recursal_valor_sentenca_total: number | null
    fase_execucao_total_processos: number | null
    fase_execucao_valor_causa_total: number | null
    fase_execucao_valor_execucao_total: number | null
    fase_inicial_por_subfase: Subfase[] | null
    fase_recursal_por_subfase: Subfase[] | null
    fase_execucao_por_subfase: Subfase[] | null
    juridico_por_comarca: ComarcaPonto[] | null
}

export type Comercial = {
    contratos: number
    contratos_anterior: number
    acoes: number
    acoes_anterior: number
    contratos_por_mes: Point[]
    acoes_por_mes: Point[]
    contratos_por_dia: Point[]
    acoes_por_dia: Point[]
}

export type Protocolo = {
    represados: number
    protocolados: number
    protocolados_anterior: number
    valor_causa: number
    valor_causa_anterior: number
    ticket_medio: number
    ticket_medio_anterior: number
    protocolados_por_mes: Point[]
    valor_causa_por_mes: Point[]
    protocolados_por_dia: Point[]
    valor_causa_por_dia: Point[]
}

export type EstrategicoResponse = {
    meta: Meta
    unidade?: string
    tem_uf?: boolean
    fontes?: { legado: boolean; lexpre: boolean }
    comercial?: Comercial
    protocolo?: Protocolo
    juridico_periodo?: Juridico
    juridico_fixo?: Juridico
}

export const UFS_NG = ['AM', 'PA', 'PB']
export const SITUACOES = [
    { value: 'ATIVO', label: 'Ativo' },
    { value: 'SUSPENSO/SOBRESTADO', label: 'Suspenso / sobrestado' },
    { value: 'ARQUIVADO', label: 'Arquivado' },
]

// "vs mês anterior" de valores já somados (v1: combinarComparativo). Sem anterior = sem comparativo.
export function comparativo(atual: number, anterior: number): number | null {
    if (!anterior) return null
    return ((atual - anterior) / anterior) * 100
}

// Ticket médio por mês (v1: divideMonthlySeriesByYear): valor de causa ÷ protocolados do mesmo mês.
export function divideSeries(numerador: Point[], denominador: Point[]): Point[] {
    const base = new Map(denominador.map((p) => [p.name, p.value]))
    return numerador
        .filter((p) => (base.get(p.name) ?? 0) > 0)
        .map((p) => ({ name: p.name, value: p.value / (base.get(p.name) ?? 1) }))
}

// Os dias de um mês ("2026-11") numa série diária "AAAA-MM-DD", em ordem.
export const diasDoMes = (pontos: Point[], mes: string): Point[] =>
    pontos.filter((p) => p.name.startsWith(`${mes}-`)).sort((a, b) => a.name.localeCompare(b.name))

// "2026-11" -> "Novembro de 2026".
export function rotuloMes(mes: string): string {
    const [ano, m] = mes.split('-').map(Number)
    const nome = MESES[m - 1] ?? ''
    return nome ? `${nome[0].toUpperCase()}${nome.slice(1)} de ${ano}` : mes
}

// As subfases como a v1 mostrava: da maior para a menor; o total soma as linhas.
export function subfases(itens: Subfase[] | null | undefined) {
    const lista = [...(itens ?? [])].sort((a, b) => b.value - a.value)
    return { itens: lista, total: lista.reduce((s, i) => s + i.value, 0) }
}

const n = (v: number | null | undefined) => v ?? 0

// Os 6 números de uma seção do Jurídico (v1: juridicoComFiltro* / juridico*).
export function numerosJuridico(j: Juridico | undefined) {
    return {
        inicialProcessos: n(j?.fase_inicial_total_processos),
        inicialValor: n(j?.fase_inicial_valor_causa_total),
        recursalProcessos: n(j?.fase_recursal_total_processos),
        recursalValor: n(j?.fase_recursal_valor_causa_total),
        recursalSentenca: n(j?.fase_recursal_valor_sentenca_total),
        execucaoProcessos: n(j?.fase_execucao_total_processos),
        execucaoValor: n(j?.fase_execucao_valor_causa_total),
        execucaoValorExecucao: n(j?.fase_execucao_valor_execucao_total),
    }
}

// Comarcas do filtro: as do Jurídico sem período (todas as que têm processo), em ordem alfabética.
export const comarcasDisponiveis = (data: EstrategicoResponse): string[] =>
    [...new Set((data.juridico_fixo?.juridico_por_comarca ?? []).map((c) => c.name).filter(Boolean))].sort((a, b) =>
        a.localeCompare(b, 'pt-BR'),
    )

// ------------------------------------------------------------------------------------------------------------------
// Seções 03 e 04 (layout novo): os 3 cards de fase e o painel de subfases (busca, ordem, gargalo e "sem subfase").
// ------------------------------------------------------------------------------------------------------------------

export type Fase = 'inicial' | 'recursal' | 'execucao'
export const FASES: Fase[] = ['inicial', 'recursal', 'execucao']
export const ROTULO_FASE: Record<Fase, string> = { inicial: 'Inicial', recursal: 'Recursal', execucao: 'Execução' }

// O valor da tabela de subfases de cada fase (a Execução só tem o valor de execução por subfase).
export const CAMPO_VALOR: Record<Fase, 'valor_causa' | 'valor_execucao'> = {
    inicial: 'valor_causa',
    recursal: 'valor_causa',
    execucao: 'valor_execucao',
}

export type ResumoFase = {
    fase: Fase
    processos: number
    valor: number
    secundario: { rotulo: string; valor: number } | null
    subfases: Subfase[]
    pctTotal: number // % dos processos das três fases
}

// Os 3 cards de uma seção do Jurídico e o total dela (o selo do cabeçalho: processos e valor de causa).
export function resumoFases(j: Juridico | undefined) {
    const x = numerosJuridico(j)
    const base: Omit<ResumoFase, 'pctTotal'>[] = [
        {
            fase: 'inicial',
            processos: x.inicialProcessos,
            valor: x.inicialValor,
            secundario: null,
            subfases: j?.fase_inicial_por_subfase ?? [],
        },
        {
            fase: 'recursal',
            processos: x.recursalProcessos,
            valor: x.recursalValor,
            secundario: { rotulo: 'Valor sentença', valor: x.recursalSentenca },
            subfases: j?.fase_recursal_por_subfase ?? [],
        },
        {
            fase: 'execucao',
            processos: x.execucaoProcessos,
            valor: x.execucaoValor,
            secundario: { rotulo: 'Valor execução', valor: x.execucaoValorExecucao },
            subfases: j?.fase_execucao_por_subfase ?? [],
        },
    ]
    const processos = base.reduce((s, f) => s + f.processos, 0)
    const valor = base.reduce((s, f) => s + f.valor, 0)
    return {
        fases: base.map((f) => ({ ...f, pctTotal: processos > 0 ? (f.processos / processos) * 100 : 0 })),
        processos,
        valor,
    }
}

export type OrdemSubfase = 'processos' | 'valor' | 'tempo' | 'nome'
export const ORDENS: { value: OrdemSubfase; label: string }[] = [
    { value: 'processos', label: 'Processos' },
    { value: 'valor', label: 'Valor' },
    { value: 'tempo', label: 'Tempo médio' },
    { value: 'nome', label: 'Nome (A–Z)' },
]

export const semSubfase = (s: Subfase) => s.name.trim().toUpperCase() === 'SEM SUBFASE'

const sem = (texto: string) =>
    texto
        .normalize('NFD')
        .replace(/\p{Diacritic}/gu, '')
        .toLowerCase()

// A tabela de uma fase: filtrada pelo nome (sem acento) e na ordem escolhida (maior primeiro; nome de A a Z).
export function listaSubfases(
    itens: Subfase[],
    campo: 'valor_causa' | 'valor_execucao',
    ordem: OrdemSubfase,
    busca: string,
): Subfase[] {
    const termo = sem(busca.trim())
    const chave: Record<OrdemSubfase, (s: Subfase) => number | string> = {
        processos: (s) => s.value,
        valor: (s) => s[campo] ?? -1,
        tempo: (s) => s.tempo_medio_dias ?? -1,
        nome: (s) => s.name,
    }
    return itens
        .filter((s) => !termo || sem(s.name).includes(termo))
        .sort((a, b) => {
            const ka = chave[ordem](a)
            const kb = chave[ordem](b)
            if (typeof ka === 'string' || typeof kb === 'string') return String(ka).localeCompare(String(kb), 'pt-BR')
            return kb - ka || a.name.localeCompare(b.name, 'pt-BR')
        })
}

// O gargalo da fase: a subfase com o maior tempo médio (null sem tempo médio).
export function gargalo(itens: Subfase[]): string | null {
    let maior: Subfase | null = null
    for (const s of itens) {
        if (s.tempo_medio_dias == null) continue
        if (!maior || s.tempo_medio_dias > (maior.tempo_medio_dias ?? 0)) maior = s
    }
    return maior?.name ?? null
}

// "R$ 34,98 mi" (o selo do cabeçalho, com 2 casas).
const brlCompacto2 = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    notation: 'compact',
    maximumFractionDigits: 2,
})
export const brlSelo = (v: number) => brlCompacto2.format(v)

// Os pontos do mapa de comarcas (quantidade e valor de causa, cada um com a UF).
export function pontosMapa(comarcas: ComarcaPonto[]) {
    return {
        quantidade: comarcas.map((c) => ({ name: c.name, value: c.value, uf: c.uf ?? null })),
        valor: comarcas.map((c) => ({ name: c.name, value: c.valor_causa ?? 0, uf: c.uf ?? null })),
    }
}

// A unidade da resposta como a do mapa ("LA_AM" e "LA_RJ" são os códigos do mock).
export function unidadeMapa(unidade: string | undefined): 'NG' | 'LA' | 'RJ' {
    if (unidade === 'LA' || unidade === 'LA_AM') return 'LA'
    if (unidade === 'RJ' || unidade === 'LA_RJ') return 'RJ'
    return 'NG'
}
