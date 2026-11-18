import type { Meta } from '../../../types/index.ts'

// Os pedaços iguais aos do Julgados Acórdãos (pontos dos gráficos, ranking e dados faltando).
export type { DadoFaltando, LinhaRelator, PontoJulgados } from '../julgados-acordaos/types.ts'

// Resposta de GET /orgs/{org}/units/{unit}/dashboards/julgados-sentencas: a DashboardResponse da rota da v1
// julgados_{NG|LA|RJ} (o model_dump) + meta. Os nomes levam o sufixo da unidade (_NG, _LA, _RJ): os números
// ficam em `stats` e os gráficos e a lista, soltos na raiz. Quem escolhe o nome certo é fields.ts.
// Fonte dos nomes e tipos: DashboardStats, DashboardResponse e JulgadosSentencaListaRow em
// apps/api/src/app/analyses/v1_dashboard_julgados_sentenca.py.
export type JulgadosSentencasResponse = {
    meta: Meta
    dashboard?: string // 'julgados_NG' | 'julgados_LA' | 'julgados_RJ'
    stats?: Record<string, unknown>
    [campo: string]: unknown // os gráficos e a lista (julgados_por_materia_NG...)
}

// Uma linha da lista "Sentenças no período" (JulgadosSentencaListaRow da v1). Datas em 'AAAA-MM-DD' ou null.
export type LinhaSentenca = {
    id: number | null
    numero_processo: string
    fase: string
    subfase: string
    status_1g: string
    uf: string
    juiz: string
    data_sentenca: string | null
    status_sentenca_embargos: string
    data_sentenca_embargos: string | null
}
