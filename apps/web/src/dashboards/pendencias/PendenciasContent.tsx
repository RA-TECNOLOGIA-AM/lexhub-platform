import { Delta } from '../../components/Delta.tsx'
import { Kpi } from '../../components/Kpi.tsx'
import { KpiSection } from '../../components/KpiSection.tsx'
import type { PendenciasResponse } from '../../data/types.ts'
import { fmt } from '../../lib/format.ts'

// Só o que é de Pendências: os KPIs. Carregar, erros e cabeçalho ficam no DashboardView.
export function PendenciasContent({ data }: { data: PendenciasResponse }) {
    const s = data.stats

    return (
        <>
            <KpiSection id="periodo" title="No período" subtitle="Pela data de entrada no setor, como na v1.">
                <Kpi
                    label="Pendências no período"
                    value={fmt.int(s.pendencias_total)}
                    note="Entraram no setor no período"
                />
                <Kpi
                    label="Resolvidas"
                    value={fmt.int(s.pendencias_resolvidas)}
                    note={<Delta value={s.comparativo_pendencias_resolvidas} />}
                />
                <Kpi
                    label="Taxa de resolução"
                    value={fmt.pct(s.pendencias_taxa_resolvidos)}
                    note={`Canceladas: ${fmt.pct(s.pendencias_taxa_canceladas)}`}
                />
                <Kpi
                    label="Tempo médio de resolução"
                    value={fmt.dias(s.media_tempo_resolvidos_pendencia)}
                    note={<Delta value={s.comparativo_tempo_medio_resolvidos_pendencia} betterWhenDown />}
                />
                <Kpi label="Tempo mediano" value={fmt.dias(s.mediana_tempo_resolvidos_pendencia)} />
            </KpiSection>

            <KpiSection id="agora" title="Situação atual do setor" subtitle="Não dependem do período selecionado.">
                <Kpi label="Abertas agora" value={fmt.int(s.pendencias_nao_resolvidas)} note="Sem filtro de período" />
                <Kpi
                    label="Abertas há mais de 5 dias"
                    value={fmt.int(s.pendencias_nao_resolvidas_com_atraso)}
                    note="Precisam de atenção"
                    tone="danger"
                />
                <Kpi label="Em triagem" value={fmt.int(s.pendencias_triagem)} note="Aguardando classificação" />
                <Kpi label="Canceladas no período" value={fmt.int(s.pendencias_canceladas)} note="Pelo próprio setor" />
            </KpiSection>
        </>
    )
}
