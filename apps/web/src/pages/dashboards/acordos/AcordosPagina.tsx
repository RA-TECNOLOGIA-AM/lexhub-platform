import { useState } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { FootRow, HeroStat, Pill } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { pickSingle, toggleFilter } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import type { ContentProps } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { AtividadesSection } from '../execucao/AtividadesSection.tsx'
import { DiligenciasSection } from '../execucao/DiligenciasSection.tsx'
import { ComarcaCard, MesAMes, ProcessosTabela, TreCard } from '../execucao/partes.tsx'
import { avisosCamposFaltando } from '../execucao/execucao.ts'
import { DadosFaltando } from '../julgados-acordaos/DadosFaltando.tsx'
import { lerAcordos } from './execucaoAcordos.ts'

const valor = (v: number | null, format: (n: number) => string) =>
    v === null ? '—' : <CountUp value={v} format={format} />

const razao = (a: number | null, b: number | null) => (a === null || !b ? null : a / b)

type Lista = 'entrada' | 'saida' | 'total'
const LISTAS: { value: Lista; label: string }[] = [
    { value: 'entrada', label: 'Entradas' },
    { value: 'saida', label: 'Saídas' },
    { value: 'total', label: 'Total' },
]

// A Execução Acordos (NG, LA e RJ), com as seções das páginas da v1 (NG/ExecucaoAcordos.tsx,
// LA/ExecucaoAcordosLA.tsx, RJ/ExecucaoAcordosRJ.tsx) no layout da V2. Carregar,
// erros, cabeçalho, período e a janela de filtros ficam no DashboardView; clicar numa subfase, matéria,
// comarca, classificação (Pré/Pós-Sentença, Judicial/Extrajudicial) ou processo liga o filtro da página.
export function AcordosPagina({ data, filters = {}, onFiltersChange }: ContentProps<V1GenericoResponse>) {
    const a = lerAcordos(data)
    const [lista, setLista] = useState<Lista>('entrada')
    const alternar =
        onFiltersChange && ((key: keyof DashboardFilters, v: string) => onFiltersChange(toggleFilter(filters, key, v)))
    const escolher =
        onFiltersChange && ((key: keyof DashboardFilters, v: string) => onFiltersChange(pickSingle(filters, key, v)))

    return (
        <div className="dsecs">
            {/* A faixa "Atenção" da Execução Condenação, com os dados do acordo: os acordos de agora (sem o período) com
                campo em branco; o modal baixa o relatório para preencher, uma aba por campo. Inclui o "valor de alçada
                final" do aviso da v1. */}
            <DadosFaltando
                avisos={avisosCamposFaltando(a.camposFaltando, 'em acordo')}
                itens={a.camposFaltando}
                base="processos em acordo"
                relatorio="campos-faltando"
                filters={filters}
            />

            <DashSection
                index={1}
                eyebrow="Negociação"
                title="Fechamento de acordo"
                subtitle="Processos que ainda estão negociando o acordo, antes de entrarem na Execução de Acordos."
            >
                <div className="grid dist-grid ex-duo">
                    <ChartCard
                        title="Valor alçada final por subfase de fechamento"
                        subtitle="Em negociação, minuta, acordo fechado ou cancelado (agora)"
                    >
                        <BarList items={a.valorFechamentoPorSubfase} format={fmt.brlShort} valueOutside wrapNames />
                    </ChartCard>
                    <ChartCard
                        title="Processos por subfase de fechamento"
                        subtitle={`${fmt.int(a.fechamentoPorSubfase.reduce((s, p) => s + p.value, 0))} processo(s) em negociação`}
                    >
                        <BarList items={a.fechamentoPorSubfase} showShare wrapNames />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Visão geral"
                title="Indicadores"
                subtitle="Volume em execução, acordos com entrada e pagos, valores de alçada final e tempos no intervalo selecionado."
            >
                {/* Como a Execução: o estoque de agora em cima; embaixo, 4 colunas em 2 linhas, com o estoque
                    inicial ocupando as duas (sem incontroverso e remanescente, que os acordos não têm). */}
                <div className="grid ex-ind-topo">
                    <HeroStat
                        label="Total em execução de acordos"
                        icon="check-circle"
                        tone="accent"
                        value={valor(a.totalEmExecucao, fmt.int)}
                        hint="Processos na fase de Execução com a etiqueta 'Acordo' ou a data de acordo fechado preenchida, agora (independente do período)."
                        footer={<FootRow left="Acordos na fase de Execução" right={<Pill>agora</Pill>} />}
                    />
                    <HeroStat
                        label="Valor total em execução de acordos"
                        icon="dollar"
                        tone="ok"
                        value={valor(a.valorTotal, fmt.brl)}
                        hint="Soma do VALOR_ALCADA_FINAL dos acordos em execução agora, independente do período. Ticket médio: valor total ÷ total em execução de acordos."
                        footer={
                            <FootRow
                                left="Ticket médio total"
                                right={
                                    <strong className="num">
                                        {fmt.brl(razao(a.valorTotal, a.totalEmExecucao) ?? 0)}
                                    </strong>
                                }
                            />
                        }
                    />
                </div>
                <div className="grid ex-ind ex-ind-4">
                    <HeroStat
                        label="Entradas de acordos"
                        icon="check-circle"
                        tone="info"
                        value={valor(a.entradas, fmt.int)}
                        hint="Processos com a etiqueta 'Acordo' cuja DATA DE EXECUÇÃO está no período, independente da fase atual (a fase muda depois, ex.: acordo pago e arquivado)."
                    />
                    <HeroStat
                        label="Acordos pagos no período"
                        icon="check-circle"
                        tone="ok"
                        value={valor(a.pagos, fmt.int)}
                        hint="Processos em Execução cuja DATA PAGAMENTO ACORDO está no período."
                    />
                    <HeroStat
                        label="Média de tempo"
                        icon="clock"
                        tone="info"
                        value={valor(a.mediaTempo, fmt.duracao)}
                        hint="Média do tempo da DATA EXECUÇÃO até a DATA PAGAMENTO ACORDO dos acordos pagos no período."
                    />
                    <HeroStat
                        className="ex-ind-alto"
                        label="Estoque inicial do período anterior"
                        icon="scale"
                        tone="neutral"
                        value={valor(a.estoqueInicial, fmt.int)}
                        hint="Estoque inicial de acordos em execução considerado para o período: a base de entradas, saídas e da TRE."
                    />
                    <HeroStat
                        label="Valor de entradas de acordos"
                        icon="dollar"
                        tone="info"
                        value={valor(a.valorEntradas, fmt.brl)}
                        below={
                            <span className="muted small">
                                Ticket médio:{' '}
                                <strong className="num">{fmt.brl(razao(a.valorEntradas, a.entradas) ?? 0)}</strong>
                            </span>
                        }
                        hint="Soma do VALOR_ALCADA_FINAL dos acordos com entrada no período (mesmo critério de 'Entradas de acordos'). Ticket médio: valor ÷ entradas."
                    />
                    <HeroStat
                        label="Valor de acordos pagos"
                        icon="dollar"
                        tone="ok"
                        value={valor(a.valorPagos, fmt.brl)}
                        hint="Soma do VALOR_ALCADA_FINAL dos processos cuja DATA PAGAMENTO ACORDO está no período."
                    />
                    <HeroStat
                        label="Mediana de tempo"
                        icon="clock"
                        tone="info"
                        value={valor(a.medianaTempo, fmt.duracao)}
                        hint="Metade dos acordos pagos no período levou até este tempo da execução ao pagamento."
                    />
                </div>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Distribuição"
                title="Matérias e subfases"
                subtitle="Acordos em execução agora por subfase, matéria, classificação e comarca; clique para filtrar a página."
            >
                <div className="grid taxas-grid">
                    <ChartCard
                        className="ex-rolagem"
                        title="Valor alçada final por subfase"
                        subtitle="Valor de alçada final por subfase atual"
                    >
                        <BarList
                            items={a.valorPorSubfase}
                            format={fmt.brlShort}
                            valueOutside
                            wrapNames
                            selected={filters.subfase}
                            onSelect={alternar && ((v) => alternar('subfase', v))}
                            selectLabel="Filtrar pela subfase"
                        />
                    </ChartCard>
                    <ChartCard
                        className="ex-rolagem"
                        title="Processos por subfase"
                        subtitle={`${a.porSubfase.length} subfase(s)`}
                        action={alternar && <Pill tone="accent">Clique para filtrar</Pill>}
                    >
                        <BarList
                            items={a.porSubfase}
                            showShare
                            wrapNames
                            selected={filters.subfase}
                            onSelect={alternar && ((v) => alternar('subfase', v))}
                            selectLabel="Filtrar pela subfase"
                        />
                    </ChartCard>
                    <TreCard tre={a.tre} />
                </div>
                <ChartCard
                    className="ex-mt"
                    title="Execução de acordos por matéria"
                    subtitle={`${fmt.int(a.porMateria.reduce((s, p) => s + p.value, 0))} acordos em execução agora · ${a.porMateria.length} matérias · clique numa matéria para filtrar a página`}
                >
                    <PieChart
                        items={a.porMateria}
                        centerLabel="acordos"
                        labels
                        selected={filters.materia}
                        onSelect={alternar && ((v) => alternar('materia', v))}
                        selectLabel="Filtrar pela matéria"
                    />
                </ChartCard>
                <div className="grid dist-grid ex-duo ex-pizzas ex-mt">
                    <ChartCard
                        title="Pré x Pós-Sentença"
                        subtitle="Pelas etiquetas do processo no LexFlow · clique para filtrar a página"
                    >
                        <PieChart
                            items={a.porSentenca}
                            centerLabel="acordos"
                            labels
                            labelsTwoLines
                            size={240}
                            selected={filters.tipo_sentenca_execucao_acordos}
                            onSelect={escolher && ((v) => escolher('tipo_sentenca_execucao_acordos', v))}
                            selectLabel="Filtrar por"
                        />
                    </ChartCard>
                    <ChartCard
                        title="Judicial x Extrajudicial"
                        subtitle="Pelas etiquetas do processo no LexFlow · clique para filtrar a página"
                    >
                        <PieChart
                            items={a.porTipoAcao}
                            centerLabel="acordos"
                            labels
                            labelsTwoLines
                            size={240}
                            selected={filters.tipo_acao_execucao_acordos}
                            onSelect={escolher && ((v) => escolher('tipo_acao_execucao_acordos', v))}
                            selectLabel="Filtrar por"
                        />
                    </ChartCard>
                </div>
                <div className="ex-mt">
                    <ComarcaCard
                        titulo="Mapa de acordos por comarca"
                        rotuloItem="acordo(s)"
                        dados={a.comarca}
                        comarcas={a.opcoes.comarcas}
                        selected={filters.comarca ?? []}
                        onSelect={alternar && ((v) => alternar('comarca', v))}
                    />
                </div>
            </DashSection>

            <DashSection
                index={4}
                eyebrow="Tendência"
                title="Entradas e saídas de acordos por mês"
                subtitle="Quantidade de acordos com entrada na execução e de acordos pagos, mês a mês (todo o histórico, sem o período)."
            >
                <div className="grid dist-grid ex-duo">
                    <ChartCard
                        title="Entradas de acordos por mês"
                        subtitle="Pela data da execução"
                        tag={<Pill>Por ano</Pill>}
                    >
                        <MesAMes pontos={a.entradasPorMes} />
                    </ChartCard>
                    <ChartCard
                        title="Saídas de acordos por mês"
                        subtitle="Acordos pagos, pela data do pagamento"
                        tag={<Pill>Por ano</Pill>}
                    >
                        <MesAMes pontos={a.pagosPorMes} />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={5}
                eyebrow="Tendência"
                title="Evolução de valores de acordos"
                subtitle="Valor de alçada final dos acordos com entrada e dos pagos, mês a mês por ano (todo o histórico, sem o período)."
            >
                <div className="grid dist-grid ex-duo">
                    <ChartCard
                        title="Valor de entrada de acordos por mês"
                        subtitle="Alçada final, pela data da execução"
                    >
                        <MesAMes pontos={a.valorEntradasPorMes} format={fmt.brl} />
                    </ChartCard>
                    <ChartCard title="Valor de acordos pagos mês a mês" subtitle="Alçada final, pela data do pagamento">
                        <MesAMes pontos={a.valorPagosPorMes} format={fmt.brl} />
                    </ChartCard>
                </div>
            </DashSection>

            <AtividadesSection
                index={6}
                setor="acordos"
                dados={a.setor}
                filters={filters}
                setFilters={onFiltersChange}
            />
            <DiligenciasSection
                index={7}
                setor="acordos"
                dados={a.setor}
                filters={filters}
                setFilters={onFiltersChange}
            />

            <DashSection
                index={8}
                eyebrow="Detalhamento"
                title="Execuções de acordo"
                subtitle="Processos com nº, UF, data da execução, valor de alçada final e subfase, com os filtros e o período da página."
            >
                <div className="ex-toolbar">
                    <Segmented label="Quais execuções" options={LISTAS} value={lista} onChange={setLista} />
                    <span className="muted small">
                        {fmt.int(a.listas[lista].length)} processo(s) ·{' '}
                        {fmt.brl(a.listas[lista].reduce((s, p) => s + (p.valor ?? 0), 0))}
                    </span>
                </div>
                <ProcessosTabela
                    processos={a.listas[lista]}
                    rotuloValor="Valor de alçada final"
                    vazio="Nenhuma execução de acordo nesse recorte."
                />
            </DashSection>
        </div>
    )
}
