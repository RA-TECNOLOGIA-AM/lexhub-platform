import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import { campo, razao, type CampoExecucao } from './fields.ts'
import type { ExecucaoResponse } from './types.ts'

// TRE como na v1 (gráfico de ponteiro): razão com 2 casas, ex.: 2,23.
const nf2 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const razaoFmt = (v: number) => nf2.format(v)

// Só o que é de Execução: os KPIs. Carregar, erros e cabeçalho ficam no DashboardView.
// Os nomes dos campos mudam por unidade (NG, LA, RJ): quem resolve é fields.ts.
// A resposta da V2 não traz comparativos com o mês anterior para Execução, por isso não há Delta.
export function ExecucaoContent({ data }: { data: ExecucaoResponse }) {
    const unit = data.meta.unit
    const v = (chave: CampoExecucao) => campo(data.stats, chave, unit)

    const entradas = v('entradas')
    const valorEntradas = v('valorEntradas')

    return (
        <>
            <KpiSection
                id="periodo"
                title="No período"
                subtitle="Entradas pela data da execução; saídas pela data de compensação do alvará."
            >
                <Kpi
                    label="Quantidade de entrada na Execução"
                    value={show(entradas, fmt.int)}
                    note="Processos que entraram na execução"
                />
                <Kpi
                    label="Valor em Execução"
                    value={show(valorEntradas, fmt.brl)}
                    note={`Ticket médio: ${show(razao(valorEntradas, entradas), fmt.brl)}`}
                />
                <Kpi
                    label="Quantidade de saída da Execução"
                    value={show(v('saidas'), fmt.int)}
                    note={`Qtd. Incontroverso: ${show(v('saidasIncontroverso'), fmt.int)}`}
                />
                <Kpi
                    label="Valor Total saída Execução"
                    value={show(v('valorSaidas'), fmt.brl)}
                    note={`Valor TED: ${show(v('valorTedSaidas'), fmt.brl)}`}
                />
                <Kpi
                    label="Valor Incontroverso"
                    value={show(v('valorIncontroverso'), fmt.brl)}
                    note="Compensado no período"
                />
                <Kpi
                    label="Taxa de Recuperação"
                    value={show(v('taxaRecuperacao'), fmt.pct)}
                    note="Valor TED ÷ valor de saída"
                />
            </KpiSection>

            <KpiSection
                id="tempo-estoque"
                title="Tempo e estoque"
                subtitle="Tempo da data da execução até a compensação do alvará."
            >
                <Kpi
                    label="Média de Tempo"
                    value={show(v('mediaTempo'), fmt.dias)}
                    note={`Mediana: ${show(v('medianaTempo'), fmt.dias)}`}
                />
                <Kpi
                    label="Estoque Inicial do período anterior"
                    value={show(v('estoqueInicial'), fmt.int)}
                    note="Base para entradas e saídas"
                />
                <Kpi label="Taxa de Redução Estoque (TRE)" value={show(v('tre'), razaoFmt)} />
            </KpiSection>

            <KpiSection
                id="valores"
                title="Valores em execução"
                subtitle="Valor ainda em aberto dos processos na fase de execução."
            >
                <Kpi label="Valor Total em execução" value={show(v('valorTotal'), fmt.brl)} />
                <Kpi
                    label="Valor Remanescente"
                    value={show(v('valorRemanescente'), fmt.brl)}
                    note="Após compensação parcial do incontroverso"
                />
                <Kpi label="Honorários" value={show(v('honorarios'), fmt.brl)} />
            </KpiSection>

            <KpiSection id="atividades" title="Atividades e prazos" subtitle="Agendamentos da execução no LexFlow.">
                <Kpi
                    label="Total de atividades"
                    value={show(v('atividadesTotal'), fmt.int)}
                    note={`Concluídas: ${show(v('atividadesConcluidas'), fmt.int)}`}
                />
                <Kpi
                    label="Vencidas"
                    value={show(v('atividadesVencidas'), fmt.int)}
                    note="Precisam de atenção"
                    tone="danger"
                />
                <Kpi label="Vencem hoje" value={show(v('atividadesVencemHoje'), fmt.int)} tone="warn" />
                <Kpi
                    label="Expedições de Alvará Cumpridas"
                    value={show(v('alvarasCumpridos'), fmt.int)}
                    note="Diligências encerradas como cumpridas"
                />
            </KpiSection>
        </>
    )
}
