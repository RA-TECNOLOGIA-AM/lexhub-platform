import type { Tone } from '../../../components/dashboard/tone.ts'
import type { DashboardFilters, Meta } from '../../../types/index.ts'

// Configurações das Vinculações (LexFlow, área Estratégico): a página admin da v1 admin/ConfiguracoesVinculacoesPage.tsx.
// A API devolve a resposta da rota /admin/configuracoes-vinculacoes da v1, só com o escritório da unidade
// (app/dashboards/configuracoes_vinculacoes.py); aqui ficam as contas que a página da v1 fazia no navegador.
// Só lógica pura (testada em vinculacoes.test.ts).

export type StatusVinculacao = 'ok' | 'incompleta' | 'erro' | 'inativa'
export type NivelProblema = 'erro' | 'incompleta'
export type ModoFluxo = 'encerra' | 'encaminha' | 'encaminha_com_motivo' | 'nao_configurado' | 'sem_configuracao'
export type SituacaoDestino = 'ok' | 'inativa' | 'inexistente' | 'outro_escritorio' | 'sem_destino'
export type FluxoEncerramento = 'cumprido' | 'nao_cumprido'

export type Destino = {
    ID_VINCULACAO: number | null
    MOTIVO: string | null
    QTD_DIAS: number | null
    SITUACAO: SituacaoDestino
    TEXTO: string
}

export type Fluxo = { MODO: ModoFluxo; MODO_LABEL: string; DESTINOS: Destino[] }

export type GatilhoEncerramento = {
    ORIGEM: 'slots' | 'flat' | 'nenhum'
    ATIVO: boolean
    FASE: string | null
    SUBFASE: string | null
    QTD_SLOTS_ATIVOS: number
}

export type GatilhoPorEncaminhamento = {
    OPCAO: string
    FLUXO?: FluxoEncerramento
    TIPO: string
    ID_VINCULACAO: number | null
    MOTIVO: string | null
    ATIVO: boolean
    FASE: string | null
    SUBFASE: string | null
}

export type Problema = { NIVEL: NivelProblema; TIPO: string; MENSAGEM: string }

export type OutraConfiguracao = { CAMPO: string; LABEL: string; VALOR: string; CONHECIDO: boolean }

export type Vinculacao = {
    ID_VINCULACAO: number
    ID_ESCRITORIO_ASSINANTE: number
    ESCRITORIO: string | null
    VINCULACAO_ATIVA: boolean
    SETOR: string | null
    ATIVIDADE: string | null
    VINCULACAO: string
    STATUS: StatusVinculacao
    TEM_CONFIGURACAO: boolean
    CONFIGURACAO_ATIVA: boolean | null
    FASE_AGENDAMENTO: string | null
    SUBFASE_AGENDAMENTO: string | null
    SITUACAO_AGENDAMENTO: string | null
    GATILHO_AGENDAMENTO_ATIVO: boolean | null
    GATILHO_ENCERRAMENTO_CUMPRIDO: GatilhoEncerramento | null
    GATILHO_ENCERRAMENTO_NAO_CUMPRIDO: GatilhoEncerramento | null
    GATILHOS_CONCLUSAO_POR_ENCAMINHAMENTO: GatilhoPorEncaminhamento[]
    CAMPOS_OBRIGATORIOS: string[]
    QTD_CAMPOS_OBRIGATORIOS: number
    REGRA_CUMPRIDO_EXIGE_ANEXO: boolean | null
    REGRA_CUMPRIDO_EXIGE_PARECER: boolean | null
    REGRA_CUMPRIDO_SEM_EXIGENCIA: boolean | null
    REGRA_NAO_CUMPRIDO_EXIGE_MOTIVO: boolean | null
    REGRA_NAO_CUMPRIDO_EXIGE_ANEXO: boolean | null
    REGRA_NAO_CUMPRIDO_EXIGE_MOTIVO_ANEXO: boolean | null
    REGRA_NAO_CUMPRIDO_NENHUMA_EXIGENCIA: boolean | null
    FLUXO_CUMPRIDO: Fluxo
    FLUXO_NAO_CUMPRIDO: Fluxo
    PROXIMA_ATIVIDADE_CUMPRIDO: string
    PROXIMA_ATIVIDADE_NAO_CUMPRIDO: string
    QTD_PROBLEMAS: number
    QTD_ERROS: number
    PROBLEMAS: string[]
    PROBLEMAS_DETALHE: Problema[]
    OUTRAS_CONFIGURACOES: OutraConfiguracao[]
    CONFIGURACAO_ATUALIZADO_EM: string | null
}

export type VinculacoesResponse = {
    meta: Meta
    total?: number
    total_com_problemas?: number
    campos_nao_reconhecidos?: string[]
    rows?: Vinculacao[]
}

// O filtro de status da página: sem = todas as ativas (o padrão da v1); 'todas' inclui as inativas.
export type FiltroStatus = 'ativas' | 'todas' | StatusVinculacao

export const STATUS_META: Record<StatusVinculacao, { label: string; tone: Tone; cor: string }> = {
    ok: { label: 'OK', tone: 'ok', cor: 'var(--ok-dot)' },
    incompleta: { label: 'Falta configurar', tone: 'warn', cor: 'var(--warn-dot)' },
    erro: { label: 'Com erro', tone: 'danger', cor: 'var(--c-danger)' },
    inativa: { label: 'Inativa', tone: 'neutral', cor: 'var(--text-faint)' },
}

export const MODO_TONE: Record<ModoFluxo, Tone> = {
    encerra: 'neutral',
    encaminha: 'info',
    encaminha_com_motivo: 'accent',
    nao_configurado: 'warn',
    sem_configuracao: 'warn',
}

// Destino que aponta para o lugar errado (pinta de vermelho, como na v1).
export const DESTINO_QUEBRADO: ReadonlySet<SituacaoDestino> = new Set(['inativa', 'inexistente', 'outro_escritorio'])

const primeiro = (v: string[] | undefined) => (v && v.length > 0 ? v[0] : null)

// Os filtros da página como a v1 os guardava: setor, status (sem = ativas) e tipo de problema.
export function lerFiltros(filters: DashboardFilters) {
    const status = primeiro(filters.status_vinculacao)
    return {
        setor: primeiro(filters.setor_vinculacao),
        status: (status ?? 'ativas') as FiltroStatus,
        problema: primeiro(filters.problema_vinculacao),
    }
}

// Recorte de setor: a base dos indicadores e do ranking de problemas (v1: `escopo`, sem o escritório).
export const doSetor = (rows: Vinculacao[], setor: string | null) =>
    setor === null ? rows : rows.filter((r) => r.SETOR === setor)

export function totais(rows: Vinculacao[]) {
    const t = { ok: 0, incompleta: 0, erro: 0, inativa: 0 }
    for (const r of rows) t[r.STATUS] += 1
    return { ...t, ativas: t.ok + t.incompleta + t.erro }
}

export const pct = (n: number, total: number) => (total > 0 ? Math.round((n / total) * 100) : 0)

// "Saúde por setor": na v1 era por escritório (todos juntos); na V2 a unidade já é o escritório, então a mesma
// barra (ok / falta configurar / com erro das ativas) vai por setor. Do mais problemático para o menos.
export function saudePorSetor(rows: Vinculacao[]) {
    const mapa = new Map<string, { ok: number; incompleta: number; erro: number }>()
    for (const r of rows) {
        if (r.STATUS === 'inativa' || !r.SETOR) continue
        const atual = mapa.get(r.SETOR) ?? { ok: 0, incompleta: 0, erro: 0 }
        atual[r.STATUS] += 1
        mapa.set(r.SETOR, atual)
    }
    return [...mapa.entries()]
        .map(([nome, c]) => ({ nome, ...c, total: c.ok + c.incompleta + c.erro }))
        .sort(
            (a, b) =>
                b.erro - a.erro || b.incompleta + b.erro - (a.incompleta + a.erro) || a.nome.localeCompare(b.nome),
        )
}

// "O que precisa de ajuste": vinculações por tipo de problema (cada tipo conta uma vez por vinculação); erros
// primeiro, depois os mais frequentes (v1: rankingProblemas).
export function rankingProblemas(rows: Vinculacao[]) {
    const mapa = new Map<string, { tipo: string; nivel: NivelProblema; vinculacoes: number }>()
    for (const r of rows) {
        const vistos = new Set<string>()
        for (const p of r.PROBLEMAS_DETALHE) {
            if (vistos.has(p.TIPO)) continue
            vistos.add(p.TIPO)
            const atual = mapa.get(p.TIPO) ?? { tipo: p.TIPO, nivel: p.NIVEL, vinculacoes: 0 }
            atual.vinculacoes += 1
            mapa.set(p.TIPO, atual)
        }
    }
    return [...mapa.values()].sort((a, b) =>
        a.nivel === b.nivel ? b.vinculacoes - a.vinculacoes : a.nivel === 'erro' ? -1 : 1,
    )
}

// A lista: status, tipo de problema e a busca (setor, atividade ou destino), sobre o recorte de setor.
export function filtrarLista(
    rows: Vinculacao[],
    { status, problema }: { status: FiltroStatus; problema: string | null },
    busca: string,
): Vinculacao[] {
    const termo = busca.trim().toLowerCase()
    return rows.filter((r) => {
        if (status === 'ativas' && r.STATUS === 'inativa') return false
        if (status !== 'ativas' && status !== 'todas' && r.STATUS !== status) return false
        if (problema && !r.PROBLEMAS_DETALHE.some((p) => p.TIPO === problema)) return false
        if (!termo) return true
        return [r.SETOR, r.ATIVIDADE, r.PROXIMA_ATIVIDADE_CUMPRIDO, r.PROXIMA_ATIVIDADE_NAO_CUMPRIDO].some((v) =>
            (v ?? '').toLowerCase().includes(termo),
        )
    })
}

export function regraCumprido(r: Vinculacao): string {
    const partes: string[] = []
    if (r.REGRA_CUMPRIDO_EXIGE_ANEXO) partes.push('exige anexo')
    if (r.REGRA_CUMPRIDO_EXIGE_PARECER) partes.push('exige parecer')
    if (r.REGRA_CUMPRIDO_SEM_EXIGENCIA) partes.push('sem exigência')
    return partes.join(', ') || 'não definida'
}

export function regraNaoCumprido(r: Vinculacao): string {
    const partes: string[] = []
    if (r.REGRA_NAO_CUMPRIDO_EXIGE_MOTIVO) partes.push('exige motivo')
    if (r.REGRA_NAO_CUMPRIDO_EXIGE_ANEXO) partes.push('exige anexo')
    if (r.REGRA_NAO_CUMPRIDO_EXIGE_MOTIVO_ANEXO) partes.push('exige motivo + anexo')
    if (r.REGRA_NAO_CUMPRIDO_NENHUMA_EXIGENCIA) partes.push('sem exigência')
    return partes.join(', ') || 'não definida'
}

export const gatilhoDoFluxo = (r: Vinculacao, fluxo: FluxoEncerramento) =>
    fluxo === 'cumprido' ? r.GATILHO_ENCERRAMENTO_CUMPRIDO : r.GATILHO_ENCERRAMENTO_NAO_CUMPRIDO

// As opções da aba "Trigger de Encerramento" de um fluxo (slot legado sem o campo = cumprido).
export const slotsDoFluxo = (r: Vinculacao, fluxo: FluxoEncerramento) =>
    r.GATILHOS_CONCLUSAO_POR_ENCAMINHAMENTO.filter((g) => (g.FLUXO ?? 'cumprido') === fluxo)

// Fluxo que encaminha sem nenhum destino (aviso "Sem destino definido").
export const semDestino = (f: Fluxo) =>
    (f.MODO === 'encaminha' || f.MODO === 'encaminha_com_motivo') && f.DESTINOS.length === 0

export const setores = (rows: Vinculacao[]) =>
    [...new Set(rows.map((r) => r.SETOR).filter((s): s is string => !!s))].sort((a, b) => a.localeCompare(b))
