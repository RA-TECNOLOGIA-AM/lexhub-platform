import type { Meta } from '../../../types/index.ts'

// Resposta de GET /orgs/{org}/units/{unit}/dashboards/julgados-acordaos: a DashboardResponse da rota da v1
// julgados_acordaos_{NG|LA|RJ} (o model_dump) + meta. Os nomes levam o sufixo da unidade (_NG, _LA, _RJ):
// os números ficam em `stats` e os gráficos e a lista, soltos na raiz. Quem escolhe o nome certo é fields.ts.
// Fonte dos nomes e tipos: DashboardStats, DashboardResponse e JulgadosAcordaoListaRow em
// apps/api/src/app/analyses/v1_dashboard_julgados.py.
export type JulgadosAcordaosResponse = {
    meta: Meta
    dashboard?: string // 'julgados_acordaos_NG' | 'julgados_acordaos_LA' | 'julgados_acordaos_RJ'
    stats?: Record<string, unknown>
    [campo: string]: unknown // os gráficos e a lista (julgados_acordao_por_materia_NG...)
}

// Um ponto dos gráficos (ChartDataPoint da v1): o que a tela usa dele.
export type PontoJulgados = {
    name: string
    value: number
    valorCausa: number | null // valor_causa: ano de ajuizamento e improcedências por comarca
    uf: string | null // uf: improcedências por comarca (a capital depende da UF)
    tempoMedioDias: number | null // tempo_medio_dias: improcedências por comarca (sentença -> acórdão)
}

// Uma linha do Ranking de Relatores (RecursalRankingMagistradoRow da v1): fav = procedentes, des =
// improcedentes, outros = extintos; taxa_sucesso = % de procedentes entre os três.
export type LinhaRelator = {
    name: string
    initials: string
    total: number
    taxa: number
    procedentes: number
    improcedentes: number
    extintos: number
    pctProcedentes: number
    pctImprocedentes: number
    pctExtintos: number
}

// Uma linha da lista "Acórdãos no período" (JulgadosAcordaoListaRow da v1). Datas em 'AAAA-MM-DD' ou null.
export type LinhaAcordao = {
    id: number | null
    numero_processo: string
    fase: string
    subfase: string
    status_2g: string
    uf: string
    relator: string
    data_acordao: string | null
    status_acordao_embargos: string
    data_acordao_embargos: string | null
}

// Um processo com informação faltando (ProcessoDadoFaltando da v1): o modal da faixa "Atenção".
export type DadoFaltando = { numero_processo: string; campo: string }
