import { Delta } from '../../../components/dashboard/Delta.tsx'
import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import { statsReader, type V1GenericoResponse } from '../v1Stats.ts'

// Só o que é do Protocolo (banco NG): os KPIs da página Protocolo NG da v1 ("Indicadores do período").
// Carregar, erros e cabeçalho ficam no DashboardView.
export function ProtocoloNgContent({ data }: { data: V1GenericoResponse }) {
    const n = statsReader(data)
    const protocolados = n('protocolos_resolvidos')
    const valorCausa = n('valor_causa_protocolo_novo')
    // Igual à v1: o ticket do servidor; sem ele, valor de causa ÷ protocolados.
    const ticket =
        n('ticket_medio_protocolos_resolvidos') ??
        n('ticket_medio_protocolado') ??
        (protocolados && valorCausa !== null ? valorCausa / protocolados : null)

    return (
        <>
            <KpiSection id="periodo" title="No período">
                <Kpi
                    label="Protocolados"
                    value={show(protocolados, fmt.int)}
                    note={<Delta value={n('comparativo_protocolos_resolvidos')} />}
                />
                <Kpi
                    label="Valor de causa protocolado"
                    value={show(valorCausa, fmt.brlShort)}
                    note={<Delta value={n('comparativo_valor_causa_protocolo')} />}
                />
                <Kpi
                    label="Ticket médio protocolado"
                    value={show(ticket, fmt.brl)}
                    note={
                        <Delta
                            value={
                                n('comparativo_ticket_medio_protocolos_resolvidos') ??
                                n('comparativo_ticket_medio_protocolado')
                            }
                        />
                    }
                />
                <Kpi
                    label="Tempo médio protocolado"
                    value={show(n('media_tempo_protocolado'), fmt.dias)}
                    note={<Delta value={n('comparativo_tempo_medio_protocolos_resolvidos')} betterWhenDown />}
                />
                <Kpi label="Tempo mediano protocolado" value={show(n('mediana_tempo_protocolado'), fmt.dias)} />
            </KpiSection>

            <KpiSection id="agora" title="Situação atual do setor" subtitle="Não dependem do período selecionado.">
                <Kpi
                    label="Represados"
                    value={show(n('nao_protocolados'), fmt.int)}
                    note="Ainda no setor, sem protocolo"
                />
            </KpiSection>

            <KpiSection id="reajuizamento" title="Reajuizamento">
                <Kpi
                    label="Protocolados de reajuizamento"
                    value={show(n('protocolados_de_reajuizamento'), fmt.int)}
                    note="No período"
                />
                <Kpi
                    label="Represados de reajuizamento"
                    value={show(n('nao_protocolados_de_reajuizamento'), fmt.int)}
                    note="Ainda no setor"
                />
            </KpiSection>
        </>
    )
}
