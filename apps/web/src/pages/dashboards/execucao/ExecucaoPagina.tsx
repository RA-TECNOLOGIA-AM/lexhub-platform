import { useState } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { ColumnChart } from '../../../components/charts/ColumnChart.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { FootRow, HeroStat, Pill } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { seriesByYear } from '../../../lib/charts.ts'
import { toggleFilter } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import type { ContentProps } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { mesNome } from '../setor/datas.ts'
import { AtividadesSection } from './AtividadesSection.tsx'
import { DiligenciasSection } from './DiligenciasSection.tsx'
import { lerExecucao } from './execucao.ts'
import { ComarcaCard, MesAMes, SemValorAviso, TreCard } from './partes.tsx'

// Número que pode faltar na resposta ('—'), com a contagem animada quando vem.
const valor = (v: number | null, format: (n: number) => string) =>
    v === null ? '—' : <CountUp value={v} format={format} />

const razao = (a: number | null, b: number | null) => (a === null || !b ? null : a / b)

const MES_CURTO = Array.from({ length: 12 }, (_, i) => mesNome(i).slice(0, 3))

// A Execução Condenação (NG, LA e RJ), com as seções das páginas da v1 (NG/Execucao.tsx, LA/Execucao_LA.tsx,
// RJ/ExecucaoRJ.tsx) no layout da V2. A LA não tem a seção Diligências (a rota da v1 não manda). Carregar, erros,
// cabeçalho, período e a janela de filtros (UF, comarca, matéria, subfase) ficam no DashboardView; clicar
// numa subfase, matéria ou comarca liga o filtro da página.
export function ExecucaoPagina({ data, filters = {}, onFiltersChange }: ContentProps<V1GenericoResponse>) {
    const e = lerExecucao(data)
    const alternar =
        onFiltersChange && ((key: keyof DashboardFilters, v: string) => onFiltersChange(toggleFilter(filters, key, v)))

    // Seção 03: entradas por mês de um ano (o seletor da v1; padrão: o mais recente).
    const anosEntrada = seriesByYear(e.entradasPorMes).map((a) => a.year)
    const [anoEscolhido, setAno] = useState<number | null>(null)
    const ano =
        anoEscolhido !== null && anosEntrada.includes(anoEscolhido) ? anoEscolhido : (anosEntrada.at(-1) ?? null)
    const doAno = (pts: typeof e.entradasPorMes) =>
        (seriesByYear(pts).find((a) => a.year === ano)?.values ?? Array(12).fill(null)).map((v) => v ?? 0)
    const qtdAno = doAno(e.entradasPorMes)
    const valorAno = doAno(e.valorEntradasPorMes)

    return (
        <div className="dsecs">
            <SemValorAviso total={e.semValor.total} processos={e.semValor.processos} campo="valor da execução" />

            <DashSection
                index={1}
                eyebrow="Visão geral"
                title="Indicadores"
                subtitle="Volume em execução, entradas, saídas, valores e tempos no intervalo selecionado."
            >
                {/* Linha 1: o estoque de agora. Linhas 2 e 3: o período, com o estoque inicial ocupando as duas. */}
                <div className="grid ex-ind-topo">
                    <HeroStat
                        label="Total em execução"
                        icon="check-circle"
                        tone="accent"
                        value={valor(e.totalEmExecucao, fmt.int)}
                        hint="Quantidade total de processos na fase de Execução agora, independente do período selecionado."
                        footer={<FootRow left="Processos na fase de Execução" right={<Pill>agora</Pill>} />}
                    />
                    <HeroStat
                        label="Valor total em execução"
                        icon="dollar"
                        tone="ok"
                        value={valor(e.valorTotal, fmt.brl)}
                        hint="Valor ainda em aberto dos processos em execução, independente do período. Quando o alvará do incontroverso já foi compensado, soma o valor remanescente em vez do valor cheio. Ticket médio: valor total ÷ total em execução."
                        footer={
                            <FootRow
                                left="Ticket médio total"
                                right={
                                    <strong className="num">
                                        {fmt.brl(razao(e.valorTotal, e.totalEmExecucao) ?? 0)}
                                    </strong>
                                }
                            />
                        }
                    />
                </div>
                <div className="grid ex-ind">
                    <HeroStat
                        label="Quantidade de entrada na execução"
                        icon="check-circle"
                        tone="info"
                        value={valor(e.entradas, fmt.int)}
                        hint="Processos que entraram na execução no período: DATA EXECUÇÃO preenchida no LexFlow dentro do intervalo."
                    />
                    <HeroStat
                        label="Valor remanescente"
                        icon="dollar"
                        tone="warn"
                        value={valor(e.valorRemanescente, fmt.brl)}
                        hint="Soma de VALOR_REMANESCENTE dos processos em execução agora (só os que já compensaram o incontroverso), independente do período."
                    />
                    <HeroStat
                        label="Quantidade de saída da execução"
                        icon="check-circle"
                        tone="ok"
                        value={valor(e.saidas, fmt.int)}
                        below={
                            e.saidasIncontroverso !== null && (
                                <span className="muted small">
                                    Qtd. incontroverso:{' '}
                                    <strong className="num">{fmt.int(e.saidasIncontroverso)}</strong>
                                </span>
                            )
                        }
                        hint="Processos com DATA_COMPENSACAO_ALVARA no período, independente da fase atual (inclui compensados e arquivados por procedência). Qtd. incontroverso: compensaram o incontroverso no período e ainda esperam o remanescente."
                    />
                    <HeroStat
                        label="Média de tempo"
                        icon="clock"
                        tone="info"
                        value={valor(e.mediaTempo, fmt.duracao)}
                        hint="Média do tempo da DATA EXECUÇÃO até a DATA DE COMPENSAÇÃO DO ALVARÁ dos processos compensados no período."
                    />
                    <HeroStat
                        className="ex-ind-alto"
                        label="Estoque inicial do período anterior"
                        icon="scale"
                        tone="neutral"
                        value={valor(e.estoqueInicial, fmt.int)}
                        hint="Estoque inicial de processos em execução considerado para o período: o saldo usado como base para acompanhar entradas, saídas e a TRE."
                    />
                    <HeroStat
                        label="Valor em execução"
                        icon="dollar"
                        tone="info"
                        value={valor(e.valorEntradas, fmt.brl)}
                        below={
                            <span className="muted small">
                                Ticket médio:{' '}
                                <strong className="num">{fmt.brl(razao(e.valorEntradas, e.entradas) ?? 0)}</strong>
                            </span>
                        }
                        hint="Valor da execução dos processos que entraram no período (o valor atualizado calculado na execução, não o valor de causa inicial). Ticket médio: valor ÷ quantidade de entrada."
                    />
                    <HeroStat
                        label="Valor incontroverso"
                        icon="dollar"
                        tone="accent"
                        value={valor(e.valorIncontroverso, fmt.brl)}
                        hint="Soma de VALOR_INCONTROVERSO dos processos com DATA_COMPENSACAO_ALVARA_INCONTROVERSO no período, mesmo que o processo siga em execução esperando o remanescente."
                    />
                    <HeroStat
                        label="Valor saída execução"
                        icon="dollar"
                        tone="ok"
                        value={valor(e.valorSaidas, fmt.brl)}
                        below={
                            e.valorTed !== null && (
                                <span className="muted small">
                                    Valor TED: <strong className="num">{fmt.brl(e.valorTed)}</strong>
                                </span>
                            )
                        }
                        hint="Valor que saiu da execução no período: o remanescente (ou o valor cheio) das compensações do alvará mais o incontroverso compensado no período, cada parcela pela sua data, sem contar duas vezes."
                    />
                    <HeroStat
                        label="Mediana de tempo"
                        icon="clock"
                        tone="info"
                        value={valor(e.medianaTempo, fmt.duracao)}
                        hint="Metade dos processos compensados no período levou até este tempo da DATA EXECUÇÃO à compensação do alvará."
                    />
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Distribuição"
                title="Matérias e subfases"
                subtitle="Processos em execução agora por subfase, matéria e comarca; clique para filtrar a página."
            >
                <div className="grid taxas-grid">
                    <ChartCard
                        className="ex-rolagem"
                        title="Valor execução por subfase"
                        subtitle="Valor de execução por subfase atual"
                    >
                        <BarList
                            items={e.valorPorSubfase}
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
                        subtitle={`${e.porSubfase.length} subfase(s)`}
                        action={alternar && <Pill tone="accent">Clique para filtrar</Pill>}
                    >
                        <BarList
                            items={e.porSubfase}
                            showShare
                            wrapNames
                            selected={filters.subfase}
                            onSelect={alternar && ((v) => alternar('subfase', v))}
                            selectLabel="Filtrar pela subfase"
                        />
                    </ChartCard>
                    <TreCard tre={e.tre} />
                </div>
                <div className="ex-mt">
                    <ComarcaCard
                        dados={e.comarca}
                        comarcas={e.opcoes.comarcas}
                        selected={filters.comarca ?? []}
                        onSelect={alternar && ((v) => alternar('comarca', v))}
                    />
                </div>
                <ChartCard
                    className="ex-mt"
                    title="Execução por matéria"
                    subtitle={`${fmt.int(e.porMateria.reduce((s, p) => s + p.value, 0))} processos em execução agora · ${e.porMateria.length} matérias · clique numa matéria para filtrar a página`}
                >
                    <PieChart
                        items={e.porMateria}
                        centerLabel="processos"
                        labels
                        legendWhenNarrow
                        selected={filters.materia}
                        onSelect={alternar && ((v) => alternar('materia', v))}
                        selectLabel="Filtrar pela matéria"
                    />
                </ChartCard>
                <ChartCard
                    className="ex-mt"
                    title="Valor remanescente mês a mês"
                    subtitle="Remanescente dos processos em execução, pelo mês em que entraram na execução"
                    tag={<Pill>Série anual (Jan – Dez)</Pill>}
                >
                    <MesAMes pontos={e.remanescentePorMes} format={fmt.brl} />
                </ChartCard>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Tendência"
                title="Entradas na execução por mês"
                subtitle="Quantidade e valor de processos que entraram na execução mês a mês (todo o histórico, sem o período)."
            >
                <div className="grid dist-grid ex-duo">
                    <ChartCard
                        title={`Entradas por mês${ano !== null ? ` · ${ano}` : ''}`}
                        subtitle="Processos pela data da execução"
                        action={
                            anosEntrada.length > 0 && (
                                <label className="field-select">
                                    <span className="sr-only">Ano</span>
                                    <select value={ano ?? ''} onChange={(ev) => setAno(Number(ev.target.value))}>
                                        {anosEntrada.map((a) => (
                                            <option key={a} value={a}>
                                                {a}
                                            </option>
                                        ))}
                                    </select>
                                </label>
                            )
                        }
                    >
                        <ColumnChart
                            height={280}
                            tooltip
                            categories={MES_CURTO}
                            series={[{ label: 'Quantidade', color: 'var(--chart-1)', values: qtdAno }]}
                        />
                    </ChartCard>
                    <ChartCard
                        title={`Valor das entradas${ano !== null ? ` · ${ano}` : ''}`}
                        subtitle="Soma do valor da execução"
                    >
                        <ColumnChart
                            height={280}
                            tooltip
                            format={fmt.brlShort}
                            categories={MES_CURTO}
                            series={[{ label: 'Valor', color: 'var(--chart-3)', values: valorAno }]}
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={4}
                eyebrow="Tendência"
                title="Evolução da saída mensal"
                subtitle="Valor de saída da execução mês a mês, por ano (todo o histórico, sem o período)."
            >
                <ChartCard
                    title="Valor de saída da execução mês a mês"
                    subtitle="Remanescente (ou valor cheio) pela compensação do alvará + incontroverso pela compensação dele"
                    tag={<Pill>Série anual (Jan – Dez)</Pill>}
                >
                    <MesAMes pontos={e.valorSaidasPorMes} format={fmt.brl} height={340} />
                </ChartCard>
            </DashSection>

            <AtividadesSection
                index={5}
                setor="condenacao"
                dados={e.setor}
                filters={filters}
                setFilters={onFiltersChange}
            />
            {e.unidade !== 'LA' && (
                <DiligenciasSection
                    index={6}
                    setor="condenacao"
                    dados={e.setor}
                    filters={filters}
                    setFilters={onFiltersChange}
                />
            )}
        </div>
    )
}
