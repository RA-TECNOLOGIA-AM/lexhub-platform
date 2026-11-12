import { Delta } from '../../../components/dashboard/Delta.tsx'
import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import { statsReader, type V1GenericoResponse } from '../v1Stats.ts'

// Só o que é da Organização de documentos (banco NG): os KPIs da página da v1 ("Indicadores do período" e
// "Tempo de resolução e pendências acumuladas"). Carregar, erros e cabeçalho ficam no DashboardView.
export function OrgDocumentosNgContent({ data }: { data: V1GenericoResponse }) {
    const n = statsReader(data)

    return (
        <>
            <KpiSection id="periodo" title="No período">
                <Kpi
                    label="Total resolvidos"
                    value={show(n('resolvidos_total'), fmt.int)}
                    note={<Delta value={n('comparativo_resolvidos_total')} />}
                />
                <Kpi
                    label="Resolvido manualmente"
                    value={show(n('organizados_manualmente'), fmt.int)}
                    note={<Delta value={n('comparativo_organizados_manualmente')} />}
                />
                <Kpi
                    label="Resolvido automaticamente"
                    value={show(n('organizados_e_peticionados_automaticamente'), fmt.int)}
                    note={<Delta value={n('comparativo_organizados_e_peticionados_automaticamente')} />}
                />
                <Kpi
                    label="Resolvidos de reajuizamento"
                    value={show(n('resolvidos_reajuizamento'), fmt.int)}
                    note={<Delta value={n('comparativo_resolvidos_reajuizamento')} />}
                />
                <Kpi
                    label="Cancelados"
                    value={show(n('cancelados'), fmt.int)}
                    note={<Delta value={n('comparativo_cancelados')} />}
                />
                <Kpi label="Tempo médio resolvidos" value={show(n('media_tempo_resolvidos'), fmt.dias)} />
                <Kpi label="Tempo mediano resolvidos" value={show(n('mediana_tempo_resolvidos'), fmt.dias)} />
            </KpiSection>

            <KpiSection id="agora" title="Situação atual do setor" subtitle="Não dependem do período selecionado.">
                <Kpi label="Represados" value={show(n('nao_organizados'), fmt.int)} note="Ainda no setor" />
                <Kpi
                    label="Retornos de Pendências"
                    value={show(n('retorno_pendencia'), fmt.int)}
                    note="Entradas vindas de Pendências"
                />
                <Kpi
                    label="Retornos da Confecção"
                    value={show(n('retorno_pet'), fmt.int)}
                    note="Entradas vindas do Peticionamento"
                />
            </KpiSection>
        </>
    )
}
