import { useParams } from 'react-router'
import { DashboardHeader } from '../../components/dashboard/DashboardHeader.tsx'
import { DashboardToolbar } from '../../components/dashboard/DashboardToolbar.tsx'
import { ErrorState } from '../../components/states/ErrorState.tsx'
import { LoadingState } from '../../components/states/LoadingState.tsx'
import { Notice } from '../../components/ui/Notice.tsx'
import { dataClient } from '../../services/client.ts'
import { DataError } from '../../services/errors.ts'
import type { Meta } from '../../types/index.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { useDashboardExport } from '../../hooks/useDashboardExport.ts'
import { useDashboardQuery } from '../../hooks/useDashboardQuery.ts'
import type { DashboardModule } from './types.ts'

// Módulo: o roteiro comum de todo dashboard. Lê período e filtros da URL, busca os dados da unidade
// e o catálogo, mostra carregando/erro, o cabeçalho com a barra e, por fim, o conteúdo próprio do dashboard.
export function DashboardView<T extends { meta: Meta }>({ module }: { module: DashboardModule<T> }) {
    const { org = '', unit = '' } = useParams()
    const hub = `/${org}/dashboards`
    const { query, search, setPeriod, setFilters } = useDashboardQuery()
    // Exporta com o período e os filtros em uso (os mesmos da tela).
    const { exportReport, notice, clearNotice } = useDashboardExport(module.key, { org, unit, ...query })
    // search na lista: mudar período ou filtros na URL busca de novo.
    const { data: result, error } = useAsync(
        () => Promise.all([module.fetch({ org, unit, ...query }), dataClient.listDashboards(org)]),
        [module, org, unit, search],
    )

    if (error) return <ErrorState error={error} backTo={hub} />
    if (!result) return <LoadingState variant="dashboard" />

    const [data, catalog] = result
    const summary = catalog.available.find((d) => d.key === module.key)
    if (!summary) return <ErrorState error={new DataError(404, 'Dashboard não encontrado')} backTo={hub} />

    // O período que o servidor usou de verdade (sem período na URL, é o padrão dele).
    const { from, to } = data.meta
    const period = from && to ? { from, to } : null

    const { Content } = module
    return (
        <>
            <DashboardHeader
                org={org}
                dashboard={summary}
                meta={data.meta}
                actions={
                    <DashboardToolbar
                        period={period}
                        onPeriodChange={setPeriod}
                        filterFields={module.filters?.(data) ?? []}
                        filters={query.filters}
                        onFiltersChange={setFilters}
                        exportTitle={summary.title}
                        exportGroups={module.exportFields ?? []}
                        canExport={summary.can_export}
                        onExport={exportReport}
                    />
                }
            />
            {notice && <Notice message={notice} onClose={clearNotice} />}
            <Content data={data} />
        </>
    )
}
