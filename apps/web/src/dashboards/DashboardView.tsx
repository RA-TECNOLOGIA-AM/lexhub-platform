import { useParams } from 'react-router'
import { DashboardHeader } from '../components/DashboardHeader.tsx'
import { ErrorState } from '../components/states/ErrorState.tsx'
import { LoadingState } from '../components/states/LoadingState.tsx'
import { dataClient } from '../data/client.ts'
import { DataError } from '../data/errors.ts'
import type { Meta } from '../data/types.ts'
import { useAsync } from '../hooks/useAsync.ts'
import type { DashboardModule } from './types.ts'

// Módulo: o roteiro comum de todo dashboard. Busca os dados da unidade e o catálogo,
// mostra carregando/erro, o cabeçalho e, por fim, o conteúdo próprio do dashboard.
export function DashboardView<T extends { meta: Meta }>({ module }: { module: DashboardModule<T> }) {
    const { org = '', unit = '' } = useParams()
    const hub = `/${org}/dashboards`
    const { data: result, error } = useAsync(
        () => Promise.all([module.fetch({ org, unit }), dataClient.listDashboards(org)]),
        [module, org, unit],
    )

    if (error) return <ErrorState error={error} backTo={hub} />
    if (!result) return <LoadingState variant="dashboard" />

    const [data, catalog] = result
    const summary = catalog.available.find((d) => d.key === module.key)
    if (!summary) return <ErrorState error={new DataError(404, 'Dashboard não encontrado')} backTo={hub} />

    const { Content } = module
    return (
        <>
            <DashboardHeader org={org} dashboard={summary} meta={data.meta} />
            <Content data={data} />
        </>
    )
}
