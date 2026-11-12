import { Delta } from '../../../components/dashboard/Delta.tsx'
import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import type { ComercialLexpreResponse } from './types.ts'

// A API manda o tempo até o protocolo em horas; na tela, em dias.
const horasEmDias = (h: number) => fmt.dias(h / 24)

// Só o que é do Comercial: os KPIs. Carregar, erros e cabeçalho ficam no DashboardView.
export function ComercialLexpreContent({ data }: { data: ComercialLexpreResponse }) {
    const s = data.stats

    return (
        <>
            <KpiSection
                id="captacao"
                title="Origem dos contratos"
                subtitle="Clientes que assinaram contrato no período, por canal de origem."
            >
                <Kpi
                    label="Total Contratos"
                    value={show(s.clientes_todos?.total, fmt.int)}
                    note={<Delta value={s.clientes_todos?.comparativo ?? null} />}
                />
                <Kpi
                    label="Ações Fechadas"
                    value={show(s.acoes_fechadas?.total, fmt.int)}
                    note={`${show(s.rubricas_reunidas_fechadas, fmt.int)} rubricas reunidas`}
                />
                <Kpi
                    label="Cancelados"
                    value={show(s.demandas_canceladas?.total, fmt.int)}
                    note={<Delta value={s.demandas_canceladas?.comparativo ?? null} betterWhenDown />}
                />
                <Kpi
                    label="Aproveitamento"
                    value={show(s.taxa_aproveitamento?.total, fmt.dec2)}
                    note="Ações fechadas por cliente assinado"
                />
                <Kpi
                    label="Campanha"
                    value={show(s.clientes_campanha?.total, fmt.int)}
                    note={<Delta value={s.clientes_campanha?.comparativo ?? null} />}
                />
                <Kpi
                    label="Indicação"
                    value={show(s.clientes_indicacao?.total, fmt.int)}
                    note={<Delta value={s.clientes_indicacao?.comparativo ?? null} />}
                />
                <Kpi
                    label="Retorno"
                    value={show(s.clientes_retorno?.total, fmt.int)}
                    note={<Delta value={s.clientes_retorno?.comparativo ?? null} />}
                />
            </KpiSection>

            <KpiSection
                id="leads"
                title="Leads"
                subtitle="Leads que entraram no período e quantos deles assinaram no mesmo período."
            >
                <Kpi
                    label="Leads Geral"
                    value={show(s.leads_geral?.total, fmt.int)}
                    note={<Delta value={s.leads_geral?.comparativo ?? null} />}
                />
                <Kpi
                    label="Taxa de Leads Geral"
                    value={show(s.taxa_leads_geral?.total, fmt.pct)}
                    note={<Delta value={s.taxa_leads_geral?.comparativo ?? null} />}
                />
                <Kpi
                    label="Leads Campanha"
                    value={show(s.leads_campanha?.total, fmt.int)}
                    note={<Delta value={s.leads_campanha?.comparativo ?? null} />}
                />
                <Kpi
                    label="Taxa de Leads Campanha"
                    value={show(s.taxa_leads_campanha?.total, fmt.pct)}
                    note={<Delta value={s.taxa_leads_campanha?.comparativo ?? null} />}
                />
            </KpiSection>

            <KpiSection
                id="protocolo"
                title="Protocolos e valor de causa"
                subtitle="Demandas protocoladas no período (pela data do protocolo)."
            >
                <Kpi
                    label="Protocolados"
                    value={show(s.protocolados?.total, fmt.int)}
                    note={<Delta value={s.protocolados?.comparativo ?? null} />}
                />
                <Kpi
                    label="Valor de Causa Protocolado"
                    value={show(s.valor_causa_protocolado?.total, fmt.brlShort)}
                    note={<Delta value={s.valor_causa_protocolado?.comparativo ?? null} />}
                />
                <Kpi
                    label="Ticket Médio Protocolado"
                    value={show(s.ticket_medio_protocolado?.total, fmt.brl)}
                    note={<Delta value={s.ticket_medio_protocolado?.comparativo ?? null} />}
                />
                <Kpi
                    label="Tempo Médio até o Protocolo"
                    value={show(s.tempo_medio_ate_protocolo_horas, horasEmDias)}
                    note="Da assinatura do contrato ao protocolo"
                />
            </KpiSection>
        </>
    )
}
