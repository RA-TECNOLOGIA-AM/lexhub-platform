import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { ColumnChart } from '../../../components/charts/ColumnChart.tsx'
import { GaugeChart } from '../../../components/charts/GaugeChart.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat, MiniStat, Pill, StackedRate } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { seriesByYear, sortByMonth, topN } from '../../../lib/charts.ts'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { CORES_ANO, MESES, diaCurto, diaLongo, mesBarra, mesNome, periodo } from '../setor/datas.ts'
import { FuncionarioPanel, type PainelLabels } from '../setor/FuncionarioPanel.tsx'
import {
    META_POR_FUNCIONARIO_V1,
    filaTone as tomDaFila,
    funcionarios,
    isPlaceholder,
    mesParcial,
    share,
} from '../setor/setor.ts'
import { lerPeticionamento } from './peticionamento.ts'

const VS = ' vs mês anterior'
const META_DIARIA_LA = 20 // meta diária do setor na LA (a do NG depende de quantos peticionaram)

// Os nomes de cada rota da v1: a NG fala em "peticionados"; a LA, em "confeccionados" e "represados".
const TERMOS = {
    ng: { Feitos: 'Peticionados', feitos: 'peticionados', Fila: 'Não peticionados', tempo: 'peticionado' },
    la: { Feitos: 'Confeccionados', feitos: 'confeccionados', Fila: 'Represados', tempo: 'confeccionados' },
}

const painel = (t: (typeof TERMOS)['ng']): PainelLabels => ({
    setor: 'Peticionamento',
    feitos: t.Feitos,
    pendentes: t.Fila,
    alerta: t.Fila.toLowerCase(),
    media: 'Média diária',
    valor: 'Valor confeccionado',
})

// Número que pode faltar na resposta ('—'), com a contagem animada quando vem.
const valor = (v: number | null, format: (n: number) => string) =>
    v === null ? '—' : <CountUp value={v} format={format} />

// O Peticionamento do banco legado (NG e RJ), com as seções da página da v1 no layout do Peticionamento
// (LexPre). Carregar, erros, cabeçalho, período e filtros ficam no DashboardView; clicar numa matéria ou num
// funcionário liga o filtro.
export function PeticionamentoLegadoContent({ data, filters = {}, onToggleFilter }: ContentProps<V1GenericoResponse>) {
    const p = lerPeticionamento(data)
    const t = TERMOS[p.la ? 'la' : 'ng']
    const unit = data.meta.unit
    // Linha "Sem matéria"/"Sem funcionário" não vira filtro (a API não teria o que procurar).
    const pick = (key: 'materia' | 'funcionario') =>
        onToggleFilter && ((name: string) => void (!isPlaceholder(name) && onToggleFilter(key, name)))
    const porMateria = pick('materia')
    const porFuncionario = pick('funcionario')

    const total = p.total ?? 0
    const fila = p.naoPeticionados ?? 0
    const pctFila = share(fila, total + fila)
    const filaTone = tomDaFila(pctFila)
    const topNao = topN(p.naoPorMateria, 1)[0]?.name ?? null
    const top10 = topN(p.porMateria)
    const top10Soma = top10.reduce((sum, m) => sum + m.value, 0)
    const pessoas = funcionarios({
        feitos: p.porFuncionario,
        pendentes: p.naoPorFuncionario,
        media: p.mediaPorFuncionario,
        valor: p.valorPorFuncionario,
    })
    const meta = META_POR_FUNCIONARIO_V1
    // Meta do setor por dia: no NG, a meta por pessoa × quem peticionou no período; na LA, fixa em 20/dia.
    const metaDiaria = p.la ? META_DIARIA_LA : meta * Math.max(1, p.mediaPorFuncionario.length)
    const taxaResolvidos = p.taxas.resolvidos ?? 0
    const taxaNao = p.taxas.naoResolvidos ?? 0

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
                subtitle={`Volume, tempos, valores e fila de ${t.Fila.toLowerCase()} no intervalo selecionado.`}
            >
                <div className="grid grid-stat">
                    <HeroStat
                        label={`Total ${t.feitos}`}
                        icon="check-circle"
                        tone="accent"
                        value={valor(p.total, fmt.int)}
                        below={<DeltaPill value={p.comparativo.total} suffix={VS} plain />}
                        hint="Processos com a petição pronta (STATUS = PROTOCOLAR), sem reajuizamento, no período: manuais + automáticos."
                        footer={
                            <FootRow
                                left={
                                    <span>
                                        Manuais <strong className="num">{fmt.int(p.manuais ?? 0)}</strong> · Automáticos{' '}
                                        <strong className="num">{fmt.int(p.automaticos ?? 0)}</strong>
                                    </span>
                                }
                            />
                        }
                    />
                    <HeroStat
                        label={t.Fila}
                        icon="x-circle"
                        tone="danger"
                        value={valor(p.naoPeticionados, fmt.int)}
                        below={<StackedRate text={`${fmt.dec1(pctFila)}%`} caption="na fila" tone={filaTone} />}
                        hint="Processos não iniciados ou com retorno de pendência, sem reajuizamento: a fila do setor agora. Não depende do período."
                        footer={
                            <FootRow
                                left="Aguardando peticionamento"
                                right={topNao && <span className="num tone-text-accent">{topNao}</span>}
                            />
                        }
                    />
                    <HeroStat
                        label="Valor confeccionado"
                        icon="dollar"
                        tone="ok"
                        value={valor(p.valor, fmt.brl)}
                        below={<DeltaPill value={p.comparativo.valor} suffix={VS} plain />}
                        hint="Soma do valor de causa (ANP usa o dano moral) dos processos com a petição pronta no período, inclusive os de reajuizamento."
                        footer={
                            <FootRow
                                left="Volume financeiro confeccionado"
                                right={<span className="num tone-text-ok">{unit}</span>}
                            />
                        }
                    />
                    <HeroStat
                        label={`Média de tempo ${t.tempo}`}
                        icon="clock"
                        tone="info"
                        value={valor(p.mediaTempo, fmt.duracao)}
                        below={<DeltaPill value={p.comparativo.mediaTempo} betterWhenDown suffix={VS} plain />}
                        hint="Tempo médio entre a entrada no setor e a petição pronta, nos processos peticionados no período."
                        footer={<FootRow left="Da entrada à petição pronta" />}
                    />
                </div>
                <div className={`grid ${p.la ? 'grid-stat' : 'grid-mini-5'} grid-mini grid-mini-stack`}>
                    <MiniStat
                        label={`${t.Feitos} manualmente`}
                        icon="users"
                        tone="accent"
                        value={valor(p.manuais, fmt.int)}
                        below={<DeltaPill value={p.comparativo.manuais} suffix={VS} plain />}
                        hint="Confeccionados por um funcionário (peticionamento automático desligado). Base da comissão."
                    />
                    <MiniStat
                        label={`${t.Feitos} automaticamente`}
                        icon="flow"
                        tone="info"
                        value={valor(p.automaticos, fmt.int)}
                        below={<DeltaPill value={p.comparativo.automaticos} suffix={VS} plain />}
                        hint="Peticionados pelo sistema (peticionamento automático ligado)."
                    />
                    {p.revisao !== null && (
                        <MiniStat
                            label="Revisão"
                            icon="eye"
                            tone="warn"
                            value={valor(p.revisao, fmt.int)}
                            below={<StackedRate text="agora" caption="não depende do período" tone="neutral" />}
                            hint="Processos em revisão (STATUS = REVISÃO), sem reajuizamento: a conferência antes do protocolo. É o total de agora, como na v1."
                        />
                    )}
                    <MiniStat
                        label="Ticket médio"
                        icon="dollar"
                        tone="ok"
                        value={valor(p.ticket, fmt.brl)}
                        below={<DeltaPill value={p.comparativo.ticket} suffix={VS} plain />}
                        hint="Valor confeccionado dividido pela quantidade de processos com a petição pronta no período."
                    />
                    <MiniStat
                        label={`Mediana de tempo ${t.tempo}`}
                        icon="clock"
                        tone="info"
                        value={valor(p.medianaTempo, fmt.duracao)}
                        below={<DeltaPill value={p.comparativo.medianaTempo} betterWhenDown suffix={VS} plain />}
                        hint="Metade dos processos peticionados no período levou até este tempo no setor."
                    />
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Indicadores"
                title={p.la ? 'Taxas do setor' : 'Taxas e reajuizamento'}
                subtitle={
                    p.la
                        ? `Resolvidos e não resolvidos sobre o total (${t.feitos} no período + fila), e o retorno ao Protocolo.`
                        : 'Resolvidos e não resolvidos sobre o total (peticionados no período + fila), e os casos de reajuizamento.'
                }
            >
                <div className="grid taxas-grid">
                    <ChartCard
                        title="Taxa de resolvidos"
                        action={
                            <Pill tone="ok">
                                {fmt.int(total)} {t.feitos}
                            </Pill>
                        }
                    >
                        <GaugeChart value={taxaResolvidos} color="var(--ok-dot)" caption="do total" />
                    </ChartCard>
                    <ChartCard
                        title="Taxa de não resolvidos"
                        action={<Pill tone={filaTone}>{fmt.int(fila)} na fila</Pill>}
                    >
                        <GaugeChart value={taxaNao} color="var(--chart-1)" caption="do total" />
                    </ChartCard>
                    {p.retornoProtocolo && (
                        <ChartCard
                            title="Taxa de retorno ao Protocolo"
                            action={
                                <Pill tone="neutral">
                                    {fmt.int(p.retornoProtocolo.retornos ?? 0)} de{' '}
                                    {fmt.int(p.retornoProtocolo.entradas ?? 0)}
                                </Pill>
                            }
                        >
                            <GaugeChart
                                value={p.retornoProtocolo.taxa ?? 0}
                                color="var(--chart-3)"
                                caption="voltaram ao Protocolo"
                            />
                        </ChartCard>
                    )}
                    {p.reajuizamento && (
                        <div className="pet-reaj">
                            <MiniStat
                                label="Resolvidos reajuizamento"
                                icon="check-circle"
                                tone="neutral"
                                value={valor(p.reajuizamento.resolvidos, fmt.int)}
                                below={<DeltaPill value={p.comparativo.reajResolvidos} suffix={VS} plain />}
                                hint="Processos de reajuizamento com a petição pronta ou em revisão no período."
                            />
                            <MiniStat
                                label="Não resolvidos reajuizamento"
                                icon="x-circle"
                                tone="neutral"
                                value={valor(p.reajuizamento.naoResolvidos, fmt.int)}
                                below={
                                    <DeltaPill
                                        value={p.comparativo.reajNaoResolvidos}
                                        betterWhenDown
                                        suffix={VS}
                                        plain
                                    />
                                }
                                hint="Processos de reajuizamento ainda sem petição no período."
                            />
                        </div>
                    )}
                </div>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Distribuições"
                title="Por matéria e por funcionário"
                subtitle="Clique em qualquer matéria à esquerda para aplicar filtro cruzado nos demais indicadores e na curva diária."
            >
                <div className="grid dist-grid">
                    <ChartCard
                        title={`Top 10 – ${t.Feitos} por matéria`}
                        subtitle={`Representatividade sobre os ${fmt.int(total)} ${t.feitos} do período`}
                        action={porMateria && <Pill tone="accent">Clique para filtrar</Pill>}
                        footer={
                            top10.length > 0 && (
                                <FootRow
                                    left={
                                        <>
                                            Top 10 soma <strong className="num">{fmt.int(top10Soma)}</strong> {t.feitos}{' '}
                                            ({fmt.dec1(share(top10Soma, total))}% do total)
                                        </>
                                    }
                                    right={`Demais matérias: ${fmt.int(Math.max(0, total - top10Soma))}`}
                                />
                            )
                        }
                    >
                        <BarList
                            items={top10}
                            total={total || undefined}
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
                            meta={meta}
                            labels={painel(t)}
                            filteredTo={filters.funcionario ?? []}
                            onFilterPerson={porFuncionario}
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={4}
                eyebrow="Produtividade"
                title={`Produção diária e ${t.Fila.toLowerCase()} por mês`}
                subtitle={`Série diária de ${t.feitos} e, por mês, o que permaneceu sem petição.`}
            >
                <div className="grid prod-grid">
                    <ChartCard
                        title="Produção diária – Peticionamento"
                        subtitle={`${periodo(data.meta.from, data.meta.to)} • Passe o cursor sobre os dias para detalhes`}
                        action={
                            <Pill tone="ok">
                                <span className="legend-dash" aria-hidden="true" /> Meta diária: {fmt.int(metaDiaria)}
                            </Pill>
                        }
                    >
                        <LineChart
                            height={320}
                            area
                            labels={p.porDia.map((d) => diaCurto(d.name))}
                            reference={{ value: metaDiaria, label: `Meta: ${fmt.int(metaDiaria)}/dia` }}
                            tooltip={{ heading: 'Dia', title: (i) => diaLongo(p.porDia[i]?.name) }}
                            series={[
                                {
                                    label: t.Feitos,
                                    color: 'var(--chart-1)',
                                    values: p.porDia.map((d) => d.value),
                                },
                            ]}
                        />
                    </ChartCard>
                    <ChartCard
                        title={`${t.Fila} por mês`}
                        action={<Pill tone={filaTone}>Retenção: {fmt.dec1(pctFila)}%</Pill>}
                        footer={
                            <div className="fstack">
                                <FootRow
                                    left="Taxa de retenção atual:"
                                    right={
                                        <span className="num">
                                            <strong className={`tone-text-${filaTone}`}>{fmt.dec1(pctFila)}%</strong>{' '}
                                            <span className="muted">
                                                ({fmt.int(fila)} de {fmt.int(total + fila)})
                                            </span>
                                        </span>
                                    }
                                />
                                <div className="fbox fbox-row small">
                                    <span className="muted">
                                        {p.naoPorMateria.length === 1 ? 'Pendência única:' : 'Principal pendência:'}
                                    </span>
                                    <strong className="num tone-text-accent">{topNao ?? 'Nenhuma'}</strong>
                                </div>
                            </div>
                        }
                    >
                        <ColumnChart
                            height={260}
                            className="col-accent"
                            caption="Mês"
                            categories={naoMes.map((m) => mesBarra(m.name))}
                            series={[
                                {
                                    label: t.Fila,
                                    color: 'var(--chart-1)',
                                    values: naoMes.map((m) => m.value),
                                },
                            ]}
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={5}
                eyebrow="Evolução"
                title={`${t.Feitos} mês a mês`}
                subtitle="Comparado por ano; não depende do período."
            >
                <ChartCard
                    title={`${t.Feitos} mês a mês`}
                    subtitle="Comparado por ano; não depende do período"
                    tag={<Pill>Por ano</Pill>}
                >
                    {anos.length === 0 ? (
                        <ChartEmpty>Sem dados no histórico.</ChartEmpty>
                    ) : (
                        <LineChart
                            height={340}
                            legend
                            emphasizeData
                            format={fmt.int}
                            labels={MESES}
                            partial={parcial !== null ? { series: ultimo, index: parcial } : undefined}
                            tooltip={{ heading: 'Mês', title: mesNome }}
                            series={anos.map((a, i) => ({
                                label: String(a.year),
                                color: CORES_ANO[(anos.length - 1 - i) % CORES_ANO.length],
                                values: a.values,
                                dashed: i < ultimo,
                                area: i === ultimo,
                            }))}
                        />
                    )}
                </ChartCard>
            </DashSection>
        </div>
    )
}
