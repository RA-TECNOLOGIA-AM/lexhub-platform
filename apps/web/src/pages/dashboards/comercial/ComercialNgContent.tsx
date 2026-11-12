import { Delta } from '../../../components/dashboard/Delta.tsx'
import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import { statsReader, type V1GenericoResponse } from '../v1Generico.ts'

// Canais de origem dos contratos, na ordem da página Comercial NG da v1 (rótulo, campo; o comparativo é
// `comparativo_<campo>`).
const ORIGENS: [string, string][] = [
    ['Campanha RA', 'clientes_campanha_RA'],
    ['Campanha NG', 'clientes_campanha_NG'],
    ['Redes Sociais', 'clientes_redes_sociais'],
    ['Indicação', 'clientes_indicacao'],
    ['Retorno', 'clientes_retorno'],
    ['Resgate', 'clientes_resgate'],
    ['Site', 'clientes_site'],
    ['Parceiros/Externos', 'clientes_parceiros_externos'],
]

// Só o que é do Comercial (banco NG): os KPIs da página Comercial NG da v1 (seções Captação, Performance e
// Protocolo). Carregar, erros e cabeçalho ficam no DashboardView.
export function ComercialNgContent({ data }: { data: V1GenericoResponse }) {
    const n = statsReader(data)
    const rubricasReunidas = n('total_rubricas_reunidas_fechadas')

    return (
        <>
            <KpiSection
                id="captacao"
                title="Origem dos contratos"
                subtitle="Clientes que assinaram contrato no período, por canal de origem."
            >
                <Kpi
                    label="Total Contratos"
                    value={show(n('clientes_todos'), fmt.int)}
                    note={<Delta value={n('comparativo_clientes_todos')} />}
                />
                <Kpi
                    label="Ações Fechadas"
                    value={show(n('acoes_fechadas'), fmt.int)}
                    note={
                        rubricasReunidas === null ? (
                            <Delta value={n('comparativo_acoes_fechadas')} />
                        ) : (
                            `${fmt.int(rubricasReunidas)} rubricas reunidas`
                        )
                    }
                />
                <Kpi
                    label="Cancelados"
                    value={show(n('clientes_cancelados'), fmt.int)}
                    note={<Delta value={n('comparativo_clientes_cancelados')} betterWhenDown />}
                />
                <Kpi
                    label="Aproveitamento"
                    value={show(n('taxa_aproveitamento'), fmt.dec2)}
                    note="Ações fechadas por cliente assinado"
                />
                {ORIGENS.map(([label, campo]) => (
                    <Kpi
                        key={campo}
                        label={label}
                        value={show(n(campo), fmt.int)}
                        note={<Delta value={n(`comparativo_${campo}`)} />}
                    />
                ))}
            </KpiSection>

            <KpiSection
                id="leads"
                title="Leads"
                subtitle="Leads que entraram no período e quantos deles assinaram no mesmo período."
            >
                <Kpi
                    label="Leads Geral"
                    value={show(n('total_leads'), fmt.int)}
                    note={<Delta value={n('comparativo_leads_geral')} />}
                />
                <Kpi
                    label="Taxa de Leads Geral"
                    value={show(n('taxa_leads_geral'), fmt.pct)}
                    note={<Delta value={n('comparativo_taxa_leads_geral')} />}
                />
                <Kpi
                    label="Leads Anúncio NG"
                    value={show(n('qtde_total_leads_anuncio_NG'), fmt.int)}
                    note={<Delta value={n('comparativo_leads_anuncio_NG')} />}
                />
                <Kpi
                    label="Taxa de Leads Anúncio NG"
                    value={show(n('taxa_leads_anuncio_NG'), fmt.pct)}
                    note={<Delta value={n('comparativo_taxa_leads_anuncio_NG')} />}
                />
            </KpiSection>

            <KpiSection
                id="protocolo"
                title="Protocolos e valor de causa"
                subtitle="Processos protocolados no período."
            >
                <Kpi
                    label="Protocolados"
                    value={show(n('protocolos_resolvidos'), fmt.int)}
                    note={<Delta value={n('comparativo_protocolos_resolvidos')} />}
                />
                <Kpi
                    label="Valor de Causa Protocolado"
                    value={show(n('valor_causa_protocolo_novo'), fmt.brlShort)}
                    note={<Delta value={n('comparativo_valor_causa_protocolo')} />}
                />
                <Kpi
                    label="Ticket Médio Protocolado"
                    value={show(n('ticket_medio_protocolado'), fmt.brl)}
                    note={<Delta value={n('comparativo_ticket_medio_protocolado')} />}
                />
                <Kpi
                    label="Tempo Médio até o Protocolo"
                    value={show(n('tempo_medio_contratacao_protocolo'), fmt.dias)}
                    note="Da assinatura do contrato ao protocolo"
                />
            </KpiSection>
        </>
    )
}
