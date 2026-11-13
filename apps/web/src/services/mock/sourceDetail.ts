import type { DashboardCatalog, SourceDetail, SourcesResponse, SyncRun } from '../../types/index.ts'
import { minAgo } from './helpers.ts'

// O detalhe de uma fonte no mock, no mesmo formato de api.source_detail (migration 20261113200000_detalhe_fonte.sql).

// Rótulo do catálogo -> chave da fonte (o mesmo ponto de partida do seed de app.dashboard_sources).
const SOURCE_OF_LABEL: Record<string, string> = { LexPre: 'lexpre', LexFlow: 'lexflow', NG: 'ng' }

// Sincronizações fictícias coerentes com o status da linha: saudável = só sucessos; atrasada = falhas no topo.
function runsFor(status: string, failures: number): SyncRun[] {
    if (status === 'waiting' || status === 'pending') return []
    return Array.from({ length: 6 }, (_, i) => {
        const failed = status === 'late' && i < failures
        const start = 180 * (status === 'late' ? 1 : 0) + 10 * i + 5
        return {
            startedAt: minAgo(start),
            finishedAt: minAgo(start - 1),
            ok: !failed,
            rows: failed ? null : 18_000 - i * 12,
            error: failed ? 'planilha não encontrada' : null,
        }
    })
}

// null = a unidade não existe ou não usa essa fonte (a tela mostra o erro, como a API).
export function sourceDetailFor(
    data: SourcesResponse,
    catalog: DashboardCatalog,
    unitCode: string,
    sourceId: string,
): SourceDetail | null {
    const unit = data.units.find((u) => u.unit.code === unitCode)
    const source = unit?.sources.find((s) => s.id === sourceId)
    if (!unit || !source) return null
    const owner =
        source.group === 'product'
            ? null
            : source.managedBy
              ? (data.units.find((u) => u.unit.name === source.managedBy)?.unit ?? null)
              : unit.unit
    return {
        unit: unit.unit,
        source,
        owner,
        dashboards: catalog.available
            .filter((d) => SOURCE_OF_LABEL[d.source] === sourceId && d.units.includes(unitCode))
            .map((d) => ({ key: d.key, name: d.title })),
        runs: runsFor(source.status, source.failures),
    }
}
