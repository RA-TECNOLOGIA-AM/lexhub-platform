import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import { pickRecursal } from './fields.ts'
import type { RecursalResponse } from './types.ts'

// Só o que é do Recursal: os KPIs. Carregar, erros e cabeçalho ficam no DashboardView.
// Os nomes dos campos mudam por unidade (NG/LA): quem escolhe é o mapa em fields.ts.
// A v1 não traz comparativo com o período anterior neste dashboard, por isso não há Delta.
export function RecursalContent({ data }: { data: RecursalResponse }) {
    const k = pickRecursal(data.stats, data.meta.unit)

    // Nota "x% das decisões"; sem o percentual, sem nota.
    const pctDecisoes = (v: number | null) => (v === null ? undefined : `${fmt.pct(v)} das decisões`)

    return (
        <>
            <KpiSection
                id="estoque"
                title="Estoque e entradas"
                subtitle="Processos na fase recursal; o estoque não depende do período selecionado."
            >
                <Kpi
                    label="Total em recursal"
                    value={show(k.estoque, fmt.int)}
                    note="Processos atualmente na fase recursal"
                />
                <Kpi
                    label="Total de entrada em recursal"
                    value={show(k.entradas, fmt.int)}
                    note="Entraram na fase no período"
                />
                <Kpi
                    label="Valor entrada acórdão Recursal"
                    value={show(k.valorEntradaAcordao, fmt.brlShort)}
                    note={k.valorEntradaAcordao === null ? undefined : show(k.valorEntradaAcordao, fmt.brl)}
                />
            </KpiSection>

            <KpiSection
                id="status"
                title="Status 1º e 2º grau"
                subtitle="Sentenças (1º grau) e acórdãos (2º grau) no período."
            >
                <Kpi
                    label="Sentenças favoráveis"
                    value={show(k.sentencaFavoravel, fmt.int)}
                    note={`Parcialmente favoráveis: ${show(k.sentencaParcialFavoravel, fmt.int)}`}
                />
                <Kpi
                    label="Sentenças desfavoráveis"
                    value={show(k.sentencaDesfavoravel, fmt.int)}
                    note={`Extintas sem mérito: ${show(k.sentencaExtincao, fmt.int)}`}
                />
                <Kpi
                    label="Acórdãos favoráveis"
                    value={show(k.acordaoFavoravel, fmt.int)}
                    note={`Parcialmente favoráveis: ${show(k.acordaoParcialFavoravel, fmt.int)}`}
                />
                <Kpi
                    label="Acórdãos desfavoráveis"
                    value={show(k.acordaoDesfavoravel, fmt.int)}
                    note={`Extintos sem mérito: ${show(k.acordaoExtincao, fmt.int)}`}
                />
            </KpiSection>

            <KpiSection
                id="decisoes"
                title="Decisões"
                subtitle="Resultado do recurso em relação à sentença, no período."
            >
                <Kpi label="Total de decisões" value={show(k.decisoes, fmt.int)} note="No período" />
                <Kpi
                    label="Mantido Ganho"
                    value={show(k.mantidoGanho, fmt.int)}
                    note={pctDecisoes(k.mantidoGanhoPct)}
                />
                <Kpi
                    label="Revertido Ganho"
                    value={show(k.revertidoGanho, fmt.int)}
                    note={pctDecisoes(k.revertidoGanhoPct)}
                />
                <Kpi
                    label="Mantido Perda"
                    value={show(k.mantidoPerda, fmt.int)}
                    note={pctDecisoes(k.mantidoPerdaPct)}
                    tone="danger"
                />
            </KpiSection>

            <KpiSection
                id="atividades"
                title="Atividades no período"
                subtitle="Atividades de recurso criadas no período e seus prazos."
            >
                <Kpi
                    label="Total de atividades"
                    value={show(k.atividades, fmt.int)}
                    note={`Em andamento: ${show(k.atividadesEmAndamento, fmt.int)}`}
                />
                <Kpi
                    label="Vencidas"
                    value={show(k.atividadesVencidas, fmt.int)}
                    note="Prazo já passou"
                    tone="danger"
                />
                <Kpi
                    label="Vencem hoje"
                    value={show(k.atividadesVencemHoje, fmt.int)}
                    note="Prazo no dia atual"
                    tone="warn"
                />
                <Kpi label="Concluídas" value={show(k.atividadesConcluidas, fmt.int)} note="Encerradas no período" />
                <Kpi
                    label="Meta de Provimento Mensal"
                    value={show(k.provimentoQtd, fmt.int)}
                    note={`Meta: ${show(k.provimentoMeta, fmt.int)} processos providos`}
                />
            </KpiSection>
        </>
    )
}
