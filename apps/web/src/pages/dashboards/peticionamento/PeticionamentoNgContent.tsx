import { Delta } from '../../../components/dashboard/Delta.tsx'
import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import { statsReader, type V1GenericoResponse } from '../v1Stats.ts'

// Só o que é do Peticionamento (banco NG): os KPIs da página Peticionamento NG da v1
// ("Indicadores do período" e "Taxas de reajuizamento"). Carregar, erros e cabeçalho ficam no DashboardView.
export function PeticionamentoNgContent({ data }: { data: V1GenericoResponse }) {
    const n = statsReader(data)

    return (
        <>
            <KpiSection id="periodo" title="No período">
                <Kpi
                    label="Total peticionados"
                    value={show(n('total_peticionados'), fmt.int)}
                    note={<Delta value={n('comparativo_peticionados')} />}
                />
                <Kpi
                    label="Peticionados manualmente"
                    value={show(n('peticionados_manualmente'), fmt.int)}
                    note={<Delta value={n('comparativo_peticionados_manualmente')} />}
                />
                <Kpi
                    label="Peticionados automaticamente"
                    value={show(n('peticionados_automaticamente'), fmt.int)}
                    note={<Delta value={n('comparativo_peticionados_automaticamente')} />}
                />
                <Kpi
                    label="Valor confeccionado"
                    value={show(n('valor_causa_confeccionado'), fmt.brlShort)}
                    note={<Delta value={n('comparativo_valor_causa_confeccionado')} />}
                />
                <Kpi
                    label="Ticket médio"
                    value={show(n('ticket_medio_confeccionado'), fmt.brl)}
                    note={<Delta value={n('comparativo_ticket_medio_confeccionado')} />}
                />
                <Kpi
                    label="Tempo médio peticionado"
                    value={show(n('media_tempo_peticionado'), fmt.dias)}
                    note={<Delta value={n('comparativo_tempo_medio_peticionado')} betterWhenDown />}
                />
                <Kpi
                    label="Tempo mediano peticionado"
                    value={show(n('mediana_tempo_peticionado'), fmt.dias)}
                    note={<Delta value={n('comparativo_mediana_tempo_pet')} betterWhenDown />}
                />
            </KpiSection>

            <KpiSection id="agora" title="Situação atual do setor" subtitle="Não dependem do período selecionado.">
                <Kpi
                    label="Não peticionados"
                    value={show(n('nao_peticionados'), fmt.int)}
                    note="Ainda no setor agora"
                />
                <Kpi label="Em revisão" value={show(n('processos_em_revisao'), fmt.int)} />
            </KpiSection>

            <KpiSection id="reajuizamento" title="Reajuizamento">
                <Kpi
                    label="Resolvidos de reajuizamento"
                    value={show(n('resolvidos_reajuizamento_pet'), fmt.int)}
                    note={<Delta value={n('comparativo_peticionados_reajuizamento')} />}
                />
                <Kpi
                    label="Não resolvidos de reajuizamento"
                    value={show(n('nao_resolvidos_reajuizamento'), fmt.int)}
                    note={<Delta value={n('comparativo_nao_peticionados_reajuizamento')} betterWhenDown />}
                />
                <Kpi label="Taxa de resolvidos" value={show(n('peticionamento_taxa_resolvidos'), fmt.pct)} />
                <Kpi label="Taxa de não resolvidos" value={show(n('peticionamento_taxa_nao_resolvidos'), fmt.pct)} />
            </KpiSection>
        </>
    )
}
