import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import { statsReader, type V1GenericoResponse } from '../v1Stats.ts'

// Só o que é de Pendências (banco NG): os KPIs da página Pendências NG da v1 ("Indicadores do período" e
// "Taxas do período"). A página da v1 não mostra comparativos aqui, por isso não há Delta.
// Carregar, erros e cabeçalho ficam no DashboardView.
export function PendenciasNgContent({ data }: { data: V1GenericoResponse }) {
    const n = statsReader(data)

    return (
        <>
            <KpiSection id="periodo" title="No período">
                <Kpi label="Total de pendências" value={show(n('pendencias_total'), fmt.int)} />
                <Kpi label="Resolvidas" value={show(n('pendencias_resolvidas'), fmt.int)} />
                <Kpi label="Canceladas" value={show(n('pendencias_canceladas'), fmt.int)} />
                <Kpi label="Triagem" value={show(n('pendencias_triagem'), fmt.int)} />
                <Kpi label="Tempo médio resolvidos" value={show(n('media_tempo_resolvidos_pendencia'), fmt.dias)} />
                <Kpi label="Tempo mediano resolvidos" value={show(n('mediana_tempo_resolvidos_pendencia'), fmt.dias)} />
            </KpiSection>

            <KpiSection id="taxas" title="Taxas do período">
                <Kpi label="Taxa de resolvidos" value={show(n('pendencias_taxa_resolvidos'), fmt.pct)} />
                <Kpi label="Taxa de não resolvidos" value={show(n('pendencias_taxa_nao_resolvidos'), fmt.pct)} />
                <Kpi label="Taxa de canceladas" value={show(n('pendencias_taxa_canceladas'), fmt.pct)} note="Máx. 5%" />
            </KpiSection>

            <KpiSection id="agora" title="Situação atual do setor" subtitle="Não dependem do período selecionado.">
                <Kpi label="Não resolvidas" value={show(n('pendencias_nao_resolvidas'), fmt.int)} />
                <Kpi
                    label="Não resolvidas há mais de 5 dias"
                    value={show(n('pendencias_nao_resolvidas_com_atraso'), fmt.int)}
                    note="Precisam de atenção"
                    tone="danger"
                />
            </KpiSection>

            <KpiSection id="reajuizamento" title="Reajuizamento">
                <Kpi
                    label="Não resolvidas de reajuizamento"
                    value={show(n('pendencias_nao_resolvidas_reajuizamento'), fmt.int)}
                />
                <Kpi
                    label="Resolvidas de reajuizamento"
                    value={show(n('pendencias_resolvidas_reajuizamento'), fmt.int)}
                />
            </KpiSection>
        </>
    )
}
