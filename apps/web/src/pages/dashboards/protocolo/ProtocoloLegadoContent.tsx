import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { ColumnChart } from '../../../components/charts/ColumnChart.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat, MiniStat, Pill, StackedRate } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { seriesByYear, sortByMonth, topN } from '../../../lib/charts.ts'
import { pickSingle } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { CORES_ANO, MESES, diaCurto, diaLongo, mesBarra, mesNome, periodo } from '../setor/datas.ts'
import { FuncionarioPanel, type PainelLabels } from '../setor/FuncionarioPanel.tsx'
import { META_POR_FUNCIONARIO_V1, funcionarios, isPlaceholder, mesParcial, share } from '../setor/setor.ts'
import { lerProtocolo } from './protocolo.ts'

const VS = ' vs mês anterior'
const PAINEL: PainelLabels = {
    setor: 'Protocolo',
    feitos: 'Protocolados',
    pendentes: 'Represados',
    alerta: 'não protocolados',
    media: 'Média diária',
    valor: 'Valor protocolado',
}

// Número que pode faltar na resposta ('—'), com a contagem animada quando vem.
const valor = (v: number | null, format: (n: number) => string) =>
    v === null ? '—' : <CountUp value={v} format={format} />

// Taxa de saída do setor (protocolados ÷ entradas): as faixas de cor do medidor da v1 (LA).
const tomTaxa = (t: number) => (t >= 85 ? 'ok' : t >= 70 ? 'warn' : 'danger')

// O Protocolo do banco legado (NG, RJ e LA), com as seções e os gráficos da página da v1. Carregar, erros,
// cabeçalho, período e filtros ficam no DashboardView; clicar numa matéria, num funcionário ou num sistema
// liga o filtro.
export function ProtocoloLegadoContent({
    data,
    filters = {},
    onToggleFilter,
    onFiltersChange,
}: ContentProps<V1GenericoResponse>) {
    const p = lerProtocolo(data)
    const unit = data.meta.unit
    // Linha "Sem matéria"/"Sem funcionário" não vira filtro (a API não teria o que procurar).
    const pick = (key: 'materia' | 'funcionario') =>
        onToggleFilter && ((name: string) => void (!isPlaceholder(name) && onToggleFilter(key, name)))
    const porMateria = pick('materia')
    const porFuncionario = pick('funcionario')
    const porSistema = onFiltersChange && ((name: string) => onFiltersChange(pickSingle(filters, 'sistema', name)))

    const protocolados = p.protocolados ?? 0
    const represados = p.represados ?? 0
    const fila = share(represados, protocolados + represados)
    const topRepresado = topN(p.naoPorMateria, 1)[0]?.name ?? null
    const top10 = topN(p.porMateria)
    const top10Soma = top10.reduce((sum, m) => sum + m.value, 0)
    const pessoas = funcionarios({
        feitos: p.porFuncionario,
        pendentes: p.naoPorFuncionario,
        media: p.mediaPorFuncionario,
        valor: p.valorPorFuncionario,
    })

    const anos = seriesByYear(p.porMes)
    const ultimo = anos.length - 1
    const parcial = ultimo >= 0 ? mesParcial(anos[ultimo].year) : null
    const naoMes = sortByMonth(p.naoPorMes)

    return (
        <div className="dsecs">
            <DashSection
                index={1}
                eyebrow="Visão geral"
                title="Indicadores do período"
                subtitle="Protocolados, represados, valores e tempos no intervalo selecionado (quando aplicável)."
            >
                <div className="grid grid-stat">
                    <HeroStat
                        label="Protocolados"
                        icon="check-circle"
                        tone="accent"
                        value={valor(p.protocolados, fmt.int)}
                        below={<DeltaPill value={p.comparativo.protocolados} suffix={VS} plain />}
                        hint={
                            p.la
                                ? 'Processos protocolados (saída do setor) no período.'
                                : 'Processos protocolados ou distribuídos no período, sem os de reajuizamento.'
                        }
                        footer={<FootRow left="Saída do setor no período" />}
                    />
                    <HeroStat
                        label="Represados"
                        icon="x-circle"
                        tone="danger"
                        value={valor(p.represados, fmt.int)}
                        below={<StackedRate text={`${fmt.dec1(fila)}%`} caption="na fila" tone="danger" />}
                        hint="Processos no setor ainda sem protocolo (não iniciados, não protocolados ou pré-protocolados). Não depende do período: é o total acumulado."
                        footer={
                            <FootRow
                                left="Aguardando protocolo"
                                right={topRepresado && <span className="num tone-text-accent">{topRepresado}</span>}
                            />
                        }
                    />
                    <HeroStat
                        label="Valor de causa protocolado"
                        icon="dollar"
                        tone="ok"
                        value={valor(p.valorCausa, fmt.brl)}
                        below={<DeltaPill value={p.comparativo.valorCausa} suffix={VS} plain />}
                        hint="Soma do valor de causa dos processos protocolados no período."
                        footer={
                            <FootRow
                                left="Volume financeiro do período"
                                right={<span className="num tone-text-ok">{unit}</span>}
                            />
                        }
                    />
                    <HeroStat
                        label="Média de tempo protocolado"
                        icon="clock"
                        tone="info"
                        value={valor(p.mediaTempo, fmt.duracao)}
                        below={<DeltaPill value={p.comparativo.mediaTempo} betterWhenDown suffix={VS} plain />}
                        hint="Tempo médio entre a entrada no setor e o protocolo, nos processos protocolados no período."
                        footer={<FootRow left="Da entrada ao protocolo" />}
                    />
                </div>
                <div className="grid grid-stat grid-mini grid-mini-stack">
                    {p.reajuizamento ? (
                        <>
                            <MiniStat
                                label="Protocolados de reajuizamento"
                                icon="check-circle"
                                tone="neutral"
                                value={valor(p.reajuizamento.protocolados, fmt.int)}
                                hint="Processos de reajuizamento protocolados ou distribuídos no período."
                            />
                            <MiniStat
                                label="Represados de reajuizamento"
                                icon="x-circle"
                                tone="neutral"
                                value={valor(p.reajuizamento.represados, fmt.int)}
                                hint="Processos de reajuizamento no setor ainda sem protocolo (total acumulado)."
                            />
                        </>
                    ) : (
                        <>
                            <MiniStat
                                label="Entradas no protocolo"
                                icon="inbox"
                                tone="neutral"
                                value={valor(p.taxa?.entradas ?? null, fmt.int)}
                                hint="Processos que entraram no setor no período."
                            />
                            <MiniStat
                                label="Taxa protocolados"
                                icon="percent"
                                tone={tomTaxa(p.taxa?.valor ?? 0)}
                                value={valor(p.taxa?.valor ?? null, (v) => `${fmt.dec1(v)}%`)}
                                hint={`Protocolados ÷ entradas no período: saíram ${fmt.int(protocolados)} de ${fmt.int(p.taxa?.entradas ?? 0)} que entraram.`}
                            />
                        </>
                    )}
                    <MiniStat
                        label="Ticket médio protocolado"
                        icon="dollar"
                        tone="ok"
                        value={valor(p.ticket, fmt.brl)}
                        below={<DeltaPill value={p.comparativo.ticket} suffix={VS} plain />}
                        hint="Valor de causa protocolado dividido pela quantidade de protocolados no período."
                    />
                    <MiniStat
                        label="Mediana de tempo protocolado"
                        icon="clock"
                        tone="info"
                        value={valor(p.medianaTempo, fmt.duracao)}
                        below={
                            p.comparativo.medianaTempo !== null && (
                                <DeltaPill value={p.comparativo.medianaTempo} betterWhenDown suffix={VS} plain />
                            )
                        }
                        hint="Metade dos processos protocolados no período levou até este tempo no setor."
                    />
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Distribuições"
                title="Por matéria e por funcionário"
                subtitle="Clique em qualquer matéria à esquerda para aplicar filtro cruzado nos demais indicadores e na curva diária."
            >
                <div className="grid dist-grid">
                    <ChartCard
                        title="Top 10 – Protocolados por matéria"
                        subtitle={`Representatividade sobre os ${fmt.int(protocolados)} protocolos do período`}
                        action={porMateria && <Pill tone="accent">Clique para filtrar</Pill>}
                        footer={
                            top10.length > 0 && (
                                <FootRow
                                    left={
                                        <>
                                            Top 10 soma <strong className="num">{fmt.int(top10Soma)}</strong> protocolos
                                            ({fmt.dec1(share(top10Soma, protocolados))}% do total)
                                        </>
                                    }
                                    right={`Demais matérias: ${fmt.int(Math.max(0, protocolados - top10Soma))}`}
                                />
                            )
                        }
                    >
                        <BarList
                            items={top10}
                            total={protocolados}
                            showShare
                            selected={filters.materia}
                            onSelect={porMateria}
                            selectLabel="Filtrar pela matéria"
                        />
                    </ChartCard>
                    <ChartCard title="Desempenho por funcionário">
                        <FuncionarioPanel
                            people={pessoas}
                            unit={unit}
                            meta={META_POR_FUNCIONARIO_V1}
                            labels={PAINEL}
                            filteredTo={filters.funcionario ?? []}
                            onFilterPerson={porFuncionario}
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Produtividade"
                title="Sistema e produção diária"
                subtitle="Participação por sistema de protocolo e série diária de protocolados."
            >
                <div className="grid ptl-prod">
                    <ChartCard
                        title="Protocolados por sistema"
                        subtitle={porSistema ? 'Clique num sistema para filtrar' : undefined}
                    >
                        <PieChart
                            items={p.porSistema}
                            size={240}
                            centerLabel="protocolados"
                            selected={filters.sistema}
                            onSelect={porSistema}
                            selectLabel="Filtrar pelo sistema"
                        />
                    </ChartCard>
                    <ChartCard
                        title="Produção diária – Protocolo"
                        subtitle={`${periodo(data.meta.from, data.meta.to)} • Passe o cursor sobre os dias para detalhes`}
                    >
                        <LineChart
                            height={320}
                            area
                            labels={p.porDia.map((d) => diaCurto(d.name))}
                            tooltip={{ heading: 'Dia', title: (i) => diaLongo(p.porDia[i]?.name) }}
                            series={[
                                {
                                    label: 'Protocolados',
                                    color: 'var(--chart-1)',
                                    values: p.porDia.map((d) => d.value),
                                },
                            ]}
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={4}
                eyebrow="Tendência"
                title="Evolução mensal"
                subtitle="Protocolados mês a mês, ano contra ano, e não protocolados pelo mês de entrada (todo o histórico)."
            >
                <div className="grid ptl-mes">
                    <ChartCard title="Protocolados mês a mês" tag={<Pill>Série Anual (Jan – Dez)</Pill>}>
                        <LineChart
                            height={340}
                            legend
                            emphasizeData
                            labels={MESES}
                            partial={parcial !== null ? { series: ultimo, index: parcial } : undefined}
                            tooltip={{ heading: 'Mês', title: mesNome }}
                            series={anos.map((a, i) => ({
                                label: String(a.year),
                                color: CORES_ANO[(anos.length - 1 - i) % CORES_ANO.length],
                                values: a.values,
                                // anos anteriores tracejados; o ano atual cheio, com o degradê
                                dashed: i < ultimo,
                                area: i === ultimo,
                            }))}
                        />
                    </ChartCard>
                    <ChartCard title="Não protocolados mês a mês" subtitle="Pelo mês de entrada no setor">
                        <ColumnChart
                            height={340}
                            className="col-accent"
                            caption="Mês de entrada"
                            categories={naoMes.map((m) => mesBarra(m.name))}
                            series={[
                                {
                                    label: 'Não protocolados',
                                    color: 'var(--chart-1)',
                                    values: naoMes.map((m) => m.value),
                                },
                            ]}
                        />
                    </ChartCard>
                </div>
            </DashSection>
        </div>
    )
}
