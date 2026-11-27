import type { CSSProperties } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { ColumnChart } from '../../../components/charts/ColumnChart.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat, MiniStat, Pill, StackedRate } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { seriesByYear, sortByMonth, topN } from '../../../lib/charts.ts'
import { fmt } from '../../../lib/format.ts'
import type { ProtocoloResponse } from '../../../types/index.ts'
import type { ContentProps } from '../types.ts'
import { CORES_ANO, MESES, diaCurto, diaLongo, mesBarra, mesNome, periodo } from '../setor/datas.ts'
import { DevolucaoCard, DevolucaoResumo } from '../setor/Devolucao.tsx'
import { FuncionarioPanel, type PainelLabels } from '../setor/FuncionarioPanel.tsx'
import { CardDuplo, RitmoDosDois } from '../setor/IndicadoresCards.tsx'
import { ReajuizamentoResumo } from '../setor/Reajuizamento.tsx'
import {
    META_POR_FUNCIONARIO_V1,
    devolucoes,
    filaTone as tomDaFila,
    funcionarios,
    isPlaceholder,
    mesParcial,
    share,
} from '../setor/setor.ts'

const PAINEL: PainelLabels = {
    setor: 'Protocolo',
    feitos: 'Protocolados',
    pendentes: 'Represados',
    alerta: 'não protocolados',
    media: 'Média diária',
    valor: 'Valor protocolado',
}

// O Protocolo (LexPre): as métricas da v1 no layout novo. Carregar, erros, cabeçalho, período e
// filtros ficam no DashboardView; clicar numa matéria ou num funcionário liga o filtro.
export function ProtocoloContent({ data, filters = {}, onToggleFilter }: ContentProps<ProtocoloResponse>) {
    const s = data.stats
    // Reajuizamento: do LexPre (demandas.reajuizamento) e, quando a página mistura o legado, + o do legado NG/RJ.
    const reajComLegado = data.fonte_indicadores === 'legado' || data.fonte_indicadores === 'misto'
    const unit = data.meta.unit
    // Linha "Sem matéria"/"Sem funcionário" não vira filtro (a API não teria o que procurar).
    const pick = (key: 'materia' | 'funcionario') =>
        onToggleFilter && ((name: string) => void (!isPlaceholder(name) && onToggleFilter(key, name)))
    const porMateria = pick('materia')
    const porFuncionario = pick('funcionario')

    const protocolados = s.protocolados_total.total
    const operacao = protocolados + s.represados // tudo o que passou pelo setor: protocolado ou na fila
    const eficiencia = share(protocolados, operacao)
    const fila = share(s.represados, operacao)
    const filaTone = tomDaFila(fila)
    const topRepresado = topN(data.represados_por_materia, 1)[0]?.name ?? null

    const pessoas = funcionarios({
        feitos: data.protocolados_por_funcionario,
        pendentes: data.represados_por_funcionario,
        media: data.media_protocolados_por_funcionario,
        valor: data.valor_causa_por_funcionario,
    })
    const meta = data.metas?.protocolados_por_funcionario ?? META_POR_FUNCIONARIO_V1
    // Meta do setor por dia = meta por pessoa x quem protocolou no período.
    const produtores = Math.max(1, data.media_protocolados_por_funcionario.length)
    const metaDiaria = meta * produtores

    const top10 = topN(data.protocolados_por_materia)
    const top10Soma = top10.reduce((sum, p) => sum + p.value, 0)
    const dev = devolucoes([
        { key: 'peticionamento', label: 'Peticionamento', value: s.devolvido_peticionamento },
        { key: 'org_doc', label: 'Org Doc', value: s.devolvido_org_doc },
        { key: 'pendencia', label: 'Pendência', value: s.devolvido_pendencia },
    ])

    const naoProtocoladosMes = sortByMonth(data.represados_por_mes)
    const anos = seriesByYear(data.protocolados_por_mes)
    const ultimo = anos.length - 1
    const parcial = ultimo >= 0 ? mesParcial(anos[ultimo].year) : null

    const devCards = [
        {
            label: 'Devolvido p/ Peticionamento',
            value: s.devolvido_peticionamento,
            comparativo: s.comparativo_devolvido_peticionamento,
            setor: 'o Peticionamento',
        },
        {
            label: 'Devolvido p/ Org Doc',
            value: s.devolvido_org_doc,
            comparativo: s.comparativo_devolvido_org_doc,
            setor: 'a Organização de Documentos',
        },
        {
            label: 'Devolvido p/ Pendência',
            value: s.devolvido_pendencia,
            comparativo: s.comparativo_devolvido_pendencia,
            setor: 'Pendências',
        },
    ]

    return (
        <div className="dsecs">
            <DashSection
                index={1}
                eyebrow="Visão geral"
                title="Indicadores do período"
                subtitle={
                    data.fonte_indicadores === 'legado'
                        ? 'Sem protocolados no LexPre neste período: números do Protocolo legado (volume, fila, tempos e valores). Devoluções continuam do LexPre.'
                        : data.fonte_indicadores === 'misto'
                          ? 'Volume, valor e tempos somam LexPre + Protocolo legado no período. Fila e devoluções são do LexPre.'
                          : 'Protocolados, represados, valores e tempos no intervalo selecionado (quando aplicável).'
                }
            >
                <div className="grid grid-stat">
                    <HeroStat
                        label="Protocolados"
                        icon="check-circle"
                        tone="accent"
                        value={<CountUp value={protocolados} format={fmt.int} />}
                        below={<DeltaPill value={s.protocolados_total.comparativo} suffix=" vs mês anterior" plain />}
                        hint="Demandas que saíram do Protocolo como protocoladas (Aguardando Despacho Inicial) no período."
                        footer={
                            <>
                                <FootRow
                                    left={<span className="tone-text-ok">{fmt.dec1(eficiencia)}% eficiência</span>}
                                />
                                <span className="progress" aria-hidden="true">
                                    <span style={{ '--w': `${eficiencia}%` } as CSSProperties} />
                                </span>
                            </>
                        }
                    />
                    <HeroStat
                        label="Represados"
                        icon="x-circle"
                        tone="danger"
                        value={<CountUp value={s.represados} format={fmt.int} />}
                        below={<StackedRate text={`${fmt.dec1(fila)}%`} caption="na fila" tone={filaTone} />}
                        hint="Demandas no Protocolo agora, ainda sem protocolo. Não depende do período."
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
                        value={<CountUp value={s.valor_causa_protocolado.total} format={fmt.brl} />}
                        below={
                            <DeltaPill value={s.valor_causa_protocolado.comparativo} suffix=" vs mês anterior" plain />
                        }
                        hint="Soma do valor de causa das demandas protocoladas no período."
                        footer={
                            <FootRow
                                left="Volume financeiro acumulado"
                                right={<span className="num tone-text-ok">{unit}</span>}
                            />
                        }
                    />
                    <CardDuplo
                        label="Tempo protocolado"
                        icon="clock"
                        tone="info"
                        hint="Da entrada no Protocolo ao protocolo, nas demandas protocoladas no período. Média e mediana (metade levou até este tempo), com a variação vs mês anterior."
                        caixas={[
                            {
                                label: 'Média',
                                value: <CountUp value={s.media_tempo_protocolado} format={fmt.duracao} />,
                                delta: s.comparativo_tempo_medio_protocolado,
                                betterWhenDown: true,
                            },
                            {
                                label: 'Mediana',
                                value: <CountUp value={s.mediana_tempo_protocolado} format={fmt.duracao} />,
                                delta: s.comparativo_mediana_tempo_protocolado,
                                betterWhenDown: true,
                            },
                        ]}
                        footer={
                            <FootRow
                                left={
                                    <RitmoDosDois
                                        media={s.comparativo_tempo_medio_protocolado}
                                        mediana={s.comparativo_mediana_tempo_protocolado}
                                    />
                                }
                                right={<span className="num muted">{data.meta.unit}</span>}
                            />
                        }
                    />
                </div>
                {/* Ticket médio + o card único de reajuizamento (como no Org. Documentos). */}
                <div className="grid grid-2 grid-mini grid-mini-stack">
                    <MiniStat
                        label="Ticket médio protocolado"
                        icon="dollar"
                        tone="ok"
                        value={<CountUp value={s.ticket_medio_protocolado.total} format={fmt.brl} />}
                        below={
                            <DeltaPill value={s.ticket_medio_protocolado.comparativo} suffix=" vs mês anterior" plain />
                        }
                        hint="Valor de causa protocolado dividido pela quantidade de protocolados no período."
                    />
                    <ReajuizamentoResumo
                        setor="Protocolo"
                        periodo={{
                            label: 'Protocolados',
                            value: s.protocolados_de_reajuizamento ?? undefined,
                            hint: `Protocolados: demandas de reajuizamento protocoladas no período${reajComLegado ? ' (LexPre + banco legado NG/RJ)' : ''}.`,
                        }}
                        fila={{
                            label: 'Represados',
                            value: s.represados_de_reajuizamento ?? undefined,
                            hint: `Represados: demandas de reajuizamento no Protocolo agora${reajComLegado ? ' (LexPre + banco legado NG/RJ)' : ''}.`,
                        }}
                    />
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Devolução"
                title="Devolvido para outros setores"
                subtitle="Demandas devolvidas do Protocolo — valores sempre totais, independentes do período selecionado."
            >
                <DevolucaoResumo dev={dev} />
                <div className="grid grid-stat-3">
                    {devCards.map((c) => (
                        <DevolucaoCard
                            key={c.label}
                            label={c.label}
                            value={c.value}
                            comparativo={c.comparativo}
                            hint={`Demandas que o Protocolo devolveu para ${c.setor} (total histórico).`}
                        />
                    ))}
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
                            meta={meta}
                            labels={PAINEL}
                            filteredTo={filters.funcionario ?? []}
                            onFilterPerson={porFuncionario}
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={4}
                eyebrow="Produtividade"
                title="Produção diária e não protocolados por mês"
                subtitle="Evolução de volumes protocolados por dia útil e acompanhamento de retenção por mês de entrada."
            >
                <div className="grid prod-grid">
                    <ChartCard
                        title="Produção diária – Protocolo"
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
                            labels={data.protocolados_por_dia.map((p) => diaCurto(p.name))}
                            reference={{ value: metaDiaria, label: `Meta: ${fmt.int(metaDiaria)}/dia` }}
                            tooltip={{ heading: 'Dia', title: (i) => diaLongo(data.protocolados_por_dia[i]?.name) }}
                            series={[
                                {
                                    label: 'Protocolados',
                                    color: 'var(--chart-1)',
                                    values: data.protocolados_por_dia.map((p) => p.value),
                                },
                            ]}
                        />
                    </ChartCard>
                    <ChartCard
                        title="Não protocolados por mês"
                        action={<Pill tone={filaTone}>Retenção: {fmt.dec1(fila)}%</Pill>}
                        footer={
                            <div className="fstack">
                                <FootRow
                                    left="Taxa de retenção atual:"
                                    right={
                                        <span className="num">
                                            <strong className={`tone-text-${filaTone}`}>{fmt.dec1(fila)}%</strong>{' '}
                                            <span className="muted">
                                                ({fmt.int(s.represados)} de {fmt.int(operacao)})
                                            </span>
                                        </span>
                                    }
                                />
                                <div className="fbox fbox-row small">
                                    <span className="muted">
                                        {data.represados_por_materia.length === 1
                                            ? 'Pendência única:'
                                            : 'Principal pendência:'}
                                    </span>
                                    <strong className="num tone-text-accent">{topRepresado ?? 'Nenhuma'}</strong>
                                </div>
                            </div>
                        }
                    >
                        <ColumnChart
                            height={260}
                            className="col-accent"
                            caption="Mês de entrada"
                            categories={naoProtocoladosMes.map((p) => mesBarra(p.name))}
                            series={[
                                {
                                    label: 'Não protocolados',
                                    color: 'var(--chart-1)',
                                    values: naoProtocoladosMes.map((p) => p.value),
                                },
                            ]}
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={5}
                eyebrow="Evolução"
                title="Protocolados mês a mês"
                subtitle="Comparado por ano; meses anteriores ao LexPre vêm do Protocolo legado."
            >
                <ChartCard
                    title="Protocolados mês a mês"
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
