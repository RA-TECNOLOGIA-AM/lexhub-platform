import type { DashboardFilters } from '../types/index.ts'

// Módulo: período e filtros de um dashboard <-> parâmetros de URL, num lugar só.
// Os nomes são os da v1/API (?from=&to=&materia=...): a URL da tela e a chamada da API usam o mesmo formato.

export type DashboardParams = { from?: string; to?: string; filters: DashboardFilters }

// Os filtros que existem (DashboardFilters). Filtro novo = acrescentar aqui e no tipo.
export const FILTER_KEYS = [
    'materia',
    'funcionario',
    'area_atuacao_id',
    'uf',
    'atendente_comercial',
    'segmento_comercial',
    'rubrica',
    'sistema',
    'origem',
    'ano_ajuizamento',
    'conv_ano_ajuizamento',
    'conv_ano_financeiro',
    'pend_ano',
    'pend_mes',
    'subfase',
    'comarca',
    'funcionario_execucao',
    'atividade_execucao',
    'situacao_execucao',
    'status_execucao',
    'diligencia_tipo_execucao',
    'diligencia_colaborador_execucao',
    'tipo_acao_execucao_acordos',
    'tipo_sentenca_execucao_acordos',
    'numero_processo_execucao_acordos',
    'funcionario_execucao_acordos',
    'atividade_execucao_acordos',
    'situacao_execucao_acordos',
    'status_execucao_acordos',
    'diligencia_tipo_execucao_acordos',
    'diligencia_colaborador_execucao_acordos',
    'escopo',
    'materia_julgados',
    'relator_julgados',
    'comarca_julgados',
    'competencia_julgados',
    'categoria_julgados',
    'uf_julgados',
    'motivo_extincao_julgados',
    'ano_ajuizamento_julgados',
    'resultado_embargos_julgados',
    'situacao_processo',
] as const satisfies readonly (keyof DashboardFilters)[]

// URL -> período e filtros. Período só vale com as duas datas e na ordem certa; senão, o servidor usa o padrão.
export function queryFromParams(params: URLSearchParams): DashboardParams {
    const filters: DashboardFilters = {}
    for (const key of FILTER_KEYS) {
        const values = params.getAll(key).filter(Boolean)
        if (values.length > 0) filters[key] = values
    }
    const from = params.get('from') ?? ''
    const to = params.get('to') ?? ''
    return from && to && from <= to ? { from, to, filters } : { filters }
}

// Período e filtros -> URL (valor repetido = vários: ?materia=ANP&materia=MORA). Vazios ficam de fora.
export function paramsFromQuery({
    from,
    to,
    filters = {},
}: {
    from?: string
    to?: string
    filters?: DashboardFilters
}) {
    const params = new URLSearchParams()
    if (from) params.set('from', from)
    if (to) params.set('to', to)
    for (const key of FILTER_KEYS) {
        for (const value of filters[key] ?? []) params.append(key, value)
    }
    return params
}
