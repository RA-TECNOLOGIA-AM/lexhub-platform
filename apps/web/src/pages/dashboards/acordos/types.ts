import type { Meta } from '../../../types/index.ts'

// Resposta do dashboard Acordos (LexFlow; na v1, "Execução de Acordos").
// É a DashboardResponse genérica da v1: os nomes dos campos levam a unidade no fim
// (ex.: total_em_execucao_acordos_NG), por isso `stats` fica como dicionário e a leitura
// passa pelo mapa de fields.ts. Tudo pode faltar: no modo mock a API devolve `stats: {}`.
export type AcordosResponse = {
    meta: Meta
    stats: Record<string, unknown>
}
