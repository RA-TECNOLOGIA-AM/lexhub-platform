import { Delta } from '../../../components/dashboard/Delta.tsx'
import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import type { PeticionamentoLexpreResponse } from './types.ts'

// Só o que é do Peticionamento: os KPIs. Carregar, erros e cabeçalho ficam no DashboardView.
export function PeticionamentoLexpreContent({ data }: { data: PeticionamentoLexpreResponse }) {
    const s = data.stats

    return (
        <>
            <KpiSection id="periodo" title="No período">
                <Kpi
                    label="Total peticionados"
                    value={show(s.total_peticionados?.total, fmt.int)}
                    note={<Delta value={s.total_peticionados?.comparativo ?? null} />}
                />
                <Kpi
                    label="Peticionados manualmente"
                    value={show(s.peticionados_manualmente?.total, fmt.int)}
                    note={<Delta value={s.peticionados_manualmente?.comparativo ?? null} />}
                />
                <Kpi
                    label="Peticionados automaticamente"
                    value={show(s.peticionados_automaticamente?.total, fmt.int)}
                    note={<Delta value={s.peticionados_automaticamente?.comparativo ?? null} />}
                />
                <Kpi
                    label="Cancelados"
                    value={show(s.cancelados?.total, fmt.int)}
                    note={<Delta value={s.cancelados?.comparativo ?? null} />}
                />
                <Kpi
                    label="Protocolados"
                    value={show(s.protocolados_total?.total, fmt.int)}
                    note={<Delta value={s.protocolados_total?.comparativo ?? null} />}
                />
                <Kpi
                    label="Valor confeccionado"
                    value={show(s.valor_causa_confeccionado?.total, fmt.brlShort)}
                    note={<Delta value={s.valor_causa_confeccionado?.comparativo ?? null} />}
                />
                <Kpi
                    label="Ticket médio"
                    value={show(s.ticket_medio_confeccionado?.total, fmt.brl)}
                    note={<Delta value={s.ticket_medio_confeccionado?.comparativo ?? null} />}
                />
                <Kpi
                    label="Tempo médio peticionado"
                    value={show(s.media_tempo_peticionado, fmt.dias)}
                    note={<Delta value={s.comparativo_tempo_medio_peticionado ?? null} betterWhenDown />}
                />
                <Kpi
                    label="Mediana de tempo peticionado"
                    value={show(s.mediana_tempo_peticionado, fmt.dias)}
                    note={<Delta value={s.comparativo_mediana_tempo_peticionado ?? null} betterWhenDown />}
                />
            </KpiSection>

            <KpiSection id="agora" title="Situação atual do setor" subtitle="Não dependem do período selecionado.">
                <Kpi label="Não peticionados" value={show(s.represados, fmt.int)} note="Ainda no setor agora" />
                {/* Total histórico; o comparativo é das devoluções no período (cair é bom). */}
                <Kpi
                    label="Devolvidos p/ Org. de documentos"
                    value={show(s.retorno_org_doc, fmt.int)}
                    note={<Delta value={s.comparativo_retorno_org_doc ?? null} betterWhenDown />}
                />
                <Kpi
                    label="Devolvidos p/ Pendências"
                    value={show(s.retorno_pendencia, fmt.int)}
                    note={<Delta value={s.comparativo_retorno_pendencia ?? null} betterWhenDown />}
                />
            </KpiSection>
        </>
    )
}
