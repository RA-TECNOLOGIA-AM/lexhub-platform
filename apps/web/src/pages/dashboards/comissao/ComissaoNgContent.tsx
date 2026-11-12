import { Delta } from '../../../components/dashboard/Delta.tsx'
import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import { statsReader, type V1GenericoResponse } from '../v1Generico.ts'

// Só o que é da Comissão Comercial (banco NG): os KPIs da página da v1 ("Cálculo e multiplicadores") e a
// base do período de onde a comissão sai. Mesmo dado do Comercial NG (na v1 as duas páginas chamam /comercial).
// Carregar, erros e cabeçalho ficam no DashboardView.
export function ComissaoNgContent({ data }: { data: V1GenericoResponse }) {
    const n = statsReader(data)
    const rubricasReunidas = n('total_rubricas_reunidas_fechadas')

    return (
        <>
            <KpiSection
                id="calculo"
                title="Cálculo da comissão"
                subtitle="Comissão base × fator multiplicador = comissão com FM."
            >
                <Kpi label="Comissão base" value={show(n('comissao_base'), fmt.brl)} />
                <Kpi label="Valor FM" value={show(n('fator_multiplicador'), fmt.fator)} />
                <Kpi label="Comissão com FM" value={show(n('comissao_com_fm'), fmt.brl)} />
            </KpiSection>

            <KpiSection
                id="proporcionais"
                title="Divisão por estado"
                subtitle="Como a comissão com FM se reparte entre AM/PA e PB."
            >
                <Kpi label="Proporcional AM/PA" value={show(n('proporcional_am_pa'), fmt.brl)} />
                <Kpi label="Proporcional PB" value={show(n('proporcional_pb'), fmt.brl)} />
            </KpiSection>

            <KpiSection id="base" title="Base do período" subtitle="Os números do Comercial de onde a comissão sai.">
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
                    label="Total Contratos"
                    value={show(n('clientes_todos'), fmt.int)}
                    note={<Delta value={n('comparativo_clientes_todos')} />}
                />
                <Kpi
                    label="Protocolados"
                    value={show(n('protocolos_resolvidos'), fmt.int)}
                    note={<Delta value={n('comparativo_protocolos_resolvidos')} />}
                />
                <Kpi
                    label="Cancelados"
                    value={show(n('clientes_cancelados'), fmt.int)}
                    note={<Delta value={n('comparativo_clientes_cancelados')} betterWhenDown />}
                />
            </KpiSection>
        </>
    )
}
