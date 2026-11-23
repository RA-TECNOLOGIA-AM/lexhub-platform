import { useState } from 'react'
import { useParams } from 'react-router'
import { DashboardHeader } from '../../components/dashboard/DashboardHeader.tsx'
import { DashboardToolbar } from '../../components/dashboard/DashboardToolbar.tsx'
import { ExportButton } from '../../components/dashboard/ExportButton.tsx'
import { PeriodPicker } from '../../components/dashboard/PeriodPicker.tsx'
import { ErrorState } from '../../components/states/ErrorState.tsx'
import { LoadingState } from '../../components/states/LoadingState.tsx'
import { Icon } from '../../components/ui/Icon.tsx'
import { Notice } from '../../components/ui/Notice.tsx'
import { commissionHtml, printHtml } from '../../lib/commissionReport.ts'
import { dataClient } from '../../services/client.ts'
import { DataError } from '../../services/errors.ts'
import type { Meta } from '../../types/index.ts'
import { toggleFilter } from '../../lib/filters.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { useAutoRefresh } from '../../hooks/useAutoRefresh.ts'
import { useDashboardExport } from '../../hooks/useDashboardExport.ts'
import { useDashboardQuery } from '../../hooks/useDashboardQuery.ts'
import { useDebouncedValue } from '../../hooks/useDebouncedValue.ts'
import { useLogDashboardView } from '../../hooks/useLogDashboardView.ts'
import { FETCH_DELAY_MS, queryFromParams } from '../../lib/dashboardQuery.ts'
import type { DashboardModule } from './types.ts'

// Mesmo prazo do cache das fontes na API (source_cache.py).
const AUTO_REFRESH_MS = 5 * 60_000

// Módulo: o roteiro comum de todo dashboard. Lê período e filtros da URL, busca os dados da unidade
// e o catálogo, mostra carregando/erro, Filtros, Período e Atualizar na topbar, a faixa de filtros ativos, o
// cabeçalho (com Gerar comissão e Exportar) e,
// por fim, o conteúdo próprio do dashboard.
export function DashboardView<T extends { meta: Meta }>({ module }: { module: DashboardModule<T> }) {
    const { org = '', unit = '' } = useParams()
    // Abriu o dashboard: vai para a Auditoria (Dashboards abertos).
    useLogDashboardView(org, unit, module.key)
    const hub = `/${org}/dashboards`
    const { query, search, setPeriod, setFilters } = useDashboardQuery()
    // Exporta com o período e os filtros em uso (os mesmos da tela).
    const { exportReport, notice, clearNotice } = useDashboardExport(module.key, { org, unit, ...query })
    // "Atualizar" soma 1 aqui e busca de novo (os números atuais ficam na tela até os novos chegarem).
    const [reload, setReload] = useState(0)
    // A busca usa a URL depois de ela ficar parada um instante: marcar várias opções seguidas na janela
    // Filtros faz UMA busca, com tudo marcado, e não uma por clique (cada uma ocupava a API com o cálculo).
    const settled = useDebouncedValue(search, FETCH_DELAY_MS)
    const asked = queryFromParams(new URLSearchParams(settled))
    // settled na lista: mudar período ou filtros na URL busca de novo (e cancela a busca anterior).
    const {
        data: result,
        error,
        loading: fetching,
    } = useAsync(
        (signal) => Promise.all([module.fetch({ org, unit, ...asked, signal }), dataClient.listDashboards(org)]),
        [module, org, unit, settled, reload],
    )
    // Esperando a URL parar de mudar também conta como "atualizando".
    const loading = fetching || settled !== search
    // A API renova o cache das fontes a cada 5 min; a tela aberta busca de novo no mesmo ritmo,
    // para os números e a "Última atualização" do cabeçalho acompanharem sem clicar em Atualizar.
    useAutoRefresh(AUTO_REFRESH_MS, () => setReload((n) => n + 1), result)

    if (error) return <ErrorState error={error} backTo={hub} />
    if (!result) return <LoadingState variant="dashboard" />

    const [data, catalog] = result
    const summary = catalog.available.find((d) => d.key === module.key)
    if (!summary) return <ErrorState error={new DataError(404, 'Dashboard não encontrado')} backTo={hub} />

    // O período que o servidor usou de verdade (sem período na URL, é o padrão dele).
    const { from, to } = data.meta
    const period = from && to ? { from, to } : null

    // Comissão: só para quem vê a de todos (Gestor/Desenvolvedor), como na v1.
    const commission = summary.can_see_commission ? module.commission?.(data) : undefined
    function printCommission() {
        if (!commission || !from || !to) return
        printHtml(
            commissionHtml({
                ...commission,
                title: commission.title ?? `Comissão — ${summary?.title ?? module.key}`,
                unit,
                from,
                to,
                generatedAt: new Date(),
            }),
        )
    }

    const { Content } = module
    return (
        <>
            {/* Filtros e Período vão na topbar; filtros ativos e Exportar, na faixa logo abaixo. */}
            <DashboardToolbar
                filterFields={module.filters?.(data, query.filters) ?? []}
                filters={query.filters}
                onFiltersChange={setFilters}
                period={<PeriodPicker value={period} onChange={setPeriod} />}
                refreshing={loading}
                onRefresh={() => setReload((n) => n + 1)}
            />
            <DashboardHeader
                org={org}
                dashboard={summary}
                meta={data.meta}
                actions={
                    <>
                        {commission && (
                            <button
                                className="btn"
                                type="button"
                                disabled={commission.rows.length === 0}
                                title={commission.rows.length === 0 ? 'Sem comissão no período' : undefined}
                                onClick={printCommission}
                            >
                                <Icon name="file-down" size={16} />
                                Gerar comissão (PDF)
                            </button>
                        )}
                        <ExportButton
                            canExport={summary.can_export}
                            title={summary.title}
                            reports={
                                module.exportReports ??
                                (module.exportFields ? [{ key: null, title: '', groups: module.exportFields }] : [])
                            }
                            initialReport={module.exportReportInicial?.(query.filters ?? {})}
                            onExport={exportReport}
                        />
                    </>
                }
            />
            {notice && <Notice message={notice} onClose={clearNotice} />}
            {/* Atualizando: cada card ganha um brilho que passa por cima (os números antigos ficam até os novos chegarem).
                display: contents — o invólucro não muda o layout do conteúdo. */}
            <div className={loading ? 'dash-content is-refreshing' : 'dash-content'} aria-busy={loading}>
                {/* Clicar numa barra (matéria, funcionário) liga ou desliga o mesmo filtro da janela Filtros. */}
                <Content
                    data={data}
                    filters={query.filters}
                    onToggleFilter={(key, value) => setFilters(toggleFilter(query.filters, key, value))}
                    onFiltersChange={setFilters}
                />
            </div>
        </>
    )
}
