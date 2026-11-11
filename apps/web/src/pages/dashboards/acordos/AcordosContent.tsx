import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import { lerAcordos } from './fields.ts'
import type { AcordosResponse } from './types.ts'

// Razão que pode faltar (divisor zero ou ausente): undefined, e a tela mostra '—'.
function razao(a: number | undefined, b: number | undefined): number | undefined {
    return a === undefined || b === undefined || b <= 0 ? undefined : a / b
}

// Só o que é de Acordos: os KPIs. Carregar, erros e cabeçalho ficam no DashboardView.
// A v1 não manda comparativo com o mês anterior para estes KPIs, por isso não há Delta.
export function AcordosContent({ data }: { data: AcordosResponse }) {
    const s = lerAcordos(data.stats ?? {}, data.meta.unit)
    const pctVencidas = razao(s.atividadesVencidas, s.atividadesTotal)

    return (
        <>
            <KpiSection
                id="em-execucao"
                title="Em execução agora"
                subtitle="Acordos na fase de Execução hoje; não dependem do período selecionado."
            >
                <Kpi
                    label="Total em Execução de Acordos"
                    value={show(s.totalEmExecucao, fmt.int)}
                    note="Etiqueta 'Acordo' ou acordo fechado"
                />
                <Kpi
                    label="Valor Total em Execução de Acordos"
                    value={show(s.valorTotalEmExecucao, fmt.brl)}
                    note={`Ticket médio: ${show(razao(s.valorTotalEmExecucao, s.totalEmExecucao), fmt.brl)}`}
                />
            </KpiSection>

            <KpiSection
                id="periodo"
                title="No período"
                subtitle="Entradas pela data de execução e pagamentos pela data de pagamento do acordo, como na v1."
            >
                <Kpi
                    label="Entradas de Acordos"
                    value={show(s.entradas, fmt.int)}
                    note="Entraram na execução no período"
                />
                <Kpi
                    label="Valor de Entradas de Acordos"
                    value={show(s.valorEntradas, fmt.brl)}
                    note={`Ticket médio: ${show(razao(s.valorEntradas, s.entradas), fmt.brl)}`}
                />
                <Kpi label="Acordos Pagos no Período" value={show(s.pagos, fmt.int)} note="Pagamento no período" />
                <Kpi label="Valor de Acordos Pagos" value={show(s.valorPagos, fmt.brl)} note="Valor de alçada final" />
                <Kpi
                    label="Média de Tempo"
                    value={show(s.mediaTempo, fmt.dias)}
                    note={`Mediana: ${show(s.medianaTempo, fmt.dias)} · da execução ao pagamento`}
                />
                <Kpi
                    label="Estoque Inicial do período anterior"
                    value={show(s.estoqueInicial, fmt.int)}
                    note="Base para entradas e saídas"
                />
                <Kpi
                    label="Taxa de Redução Estoque (TRE)"
                    value={show(s.tre, fmt.pct)}
                    note="Positiva = estoque diminuiu"
                />
            </KpiSection>

            <KpiSection
                id="atividades"
                title="Atividades no período"
                subtitle="Agendamentos do setor ACORDOS criados no período."
            >
                <Kpi
                    label="Total de atividades"
                    value={show(s.atividadesTotal, fmt.int)}
                    note={`Em andamento: ${show(s.atividadesEmAndamento, fmt.int)}`}
                />
                <Kpi
                    label="Vencidas"
                    value={show(s.atividadesVencidas, fmt.int)}
                    note={pctVencidas === undefined ? undefined : `${fmt.pct(pctVencidas * 100)} do total`}
                    tone="danger"
                />
                <Kpi
                    label="Vencem hoje"
                    value={show(s.atividadesVencemHoje, fmt.int)}
                    note="Prazo no dia atual"
                    tone="warn"
                />
                <Kpi label="Concluídas" value={show(s.atividadesConcluidas, fmt.int)} note="Encerradas no período" />
            </KpiSection>

            <KpiSection
                id="diligencias"
                title="Diligências"
                subtitle="Diligências de expedição de alvará e o valor realizado com elas no período."
            >
                <Kpi
                    label="Diligências de Expedição de Alvará"
                    value={show(s.alvaraDiligencias, fmt.int)}
                    note={`De ${show(s.diligenciasTotal, fmt.int)} diligências no período`}
                />
                <Kpi
                    label="Expedições de Alvará Cumpridas"
                    value={show(s.alvaraCumpridas, fmt.int)}
                    note="Encerradas como cumpridas"
                />
                <Kpi
                    label="Valor Realizado (Alvará)"
                    value={show(s.alvaraValorRealizado, fmt.brl)}
                    note="Alçada final, uma vez por processo"
                />
            </KpiSection>
        </>
    )
}
