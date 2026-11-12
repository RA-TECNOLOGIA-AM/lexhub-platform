import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import { statsReader, type V1GenericoResponse } from '../v1Generico.ts'

// Campos do Marketing NG na v1 levam o prefixo `marketing_ng_`.
const P = 'marketing_ng_'

// Só o que é do Marketing (banco NG): os KPIs da página Marketing NG da v1 (Facebook Ads, Funil de Pipeline e
// Fechamento Campanhas). Carregar, erros e cabeçalho ficam no DashboardView.
export function MarketingNgContent({ data }: { data: V1GenericoResponse }) {
    const ler = statsReader(data)
    const n = (campo: string) => ler(P + campo)

    return (
        <>
            <KpiSection id="facebook" title="Facebook Ads" subtitle="Investimento no período e retorno.">
                <Kpi label="Valor gasto" value={show(n('facebook_valor_gasto'), fmt.brl)} />
                <Kpi label="CAC Campanha" value={show(n('facebook_cac_campanha'), fmt.brl)} />
                <Kpi label="CAC Geral" value={show(n('facebook_cac_geral'), fmt.brl)} />
                <Kpi label="ROAS Campanha" value={show(n('facebook_roas_campanha'), fmt.dec2)} />
                <Kpi label="ROAS Geral" value={show(n('facebook_roas_geral'), fmt.dec2)} />
            </KpiSection>

            <KpiSection id="funil" title="Funil de pipeline">
                <Kpi label="Clientes de campanha" value={show(n('clientes_campanha'), fmt.int)} />
                <Kpi label="Leads" value={show(n('leads'), fmt.int)} />
                <Kpi label="Indicação ativa" value={show(n('indicacao_ativa'), fmt.int)} />
                <Kpi label="Indicação passiva" value={show(n('indicacao_passiva'), fmt.int)} />
                <Kpi label="Retorno ativa" value={show(n('retorno_ativa'), fmt.int)} />
                <Kpi label="Retorno passiva" value={show(n('retorno_passiva'), fmt.int)} />
            </KpiSection>

            {(['ra', 'ng'] as const).map((c) => (
                <KpiSection key={c} id={`campanha-${c}`} title={`Fechamento — Campanha ${c.toUpperCase()}`}>
                    {/* A v1 mostra a conversão da campanha no lugar do comparativo; aqui, como texto. */}
                    <Kpi
                        label="Clientes"
                        value={show(n(`campanha_${c}`), fmt.int)}
                        note={`Conversão: ${show(n(`conversao_${c}`), fmt.pct)}`}
                    />
                    <Kpi label="Protocolados" value={show(n(`protocolados_${c}`), fmt.int)} />
                    <Kpi label="Valor de causa" value={show(n(`valor_causa_${c}`), fmt.brlShort)} />
                    <Kpi label="Ticket médio" value={show(n(`ticket_medio_${c}`), fmt.brl)} />
                </KpiSection>
            ))}
        </>
    )
}
