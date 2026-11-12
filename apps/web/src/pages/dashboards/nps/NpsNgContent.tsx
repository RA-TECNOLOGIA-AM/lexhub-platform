import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import { statsReader, type V1GenericoResponse } from '../v1Stats.ts'

// NPS vai de -100 a 100 (% promotores − % detratores); sem casa decimal, como a v1.
const nps = (v: number) => fmt.int(v)

// Só o que é do NPS (banco NG): os KPIs da página NPS NG da v1 ("Indicadores do período").
// A v1 não traz comparativo com o período anterior aqui, por isso não há Delta.
// Carregar, erros e cabeçalho ficam no DashboardView.
export function NpsNgContent({ data }: { data: V1GenericoResponse }) {
    const n = statsReader(data)

    return (
        <KpiSection id="periodo" title="No período" subtitle="Respostas da pesquisa de satisfação no período.">
            <Kpi label="NPS" value={show(n('nps_score'), nps)} note="% promotores − % detratores" />
            <Kpi label="Total de respostas" value={show(n('nps_total_respostas'), fmt.int)} />
            <Kpi label="Promotores" value={show(n('nps_total_promotores'), fmt.int)} note="Notas 9 e 10" />
            <Kpi label="Neutros" value={show(n('nps_total_neutros'), fmt.int)} note="Notas 7 e 8" />
            <Kpi
                label="Detratores"
                value={show(n('nps_total_detratores'), fmt.int)}
                note="Notas de 0 a 6"
                tone="danger"
            />
            <Kpi
                label="Taxa de confiança"
                value={show(n('nps_taxa_confianca'), fmt.pct)}
                note="Respostas com confiança 7 ou mais"
            />
        </KpiSection>
    )
}
