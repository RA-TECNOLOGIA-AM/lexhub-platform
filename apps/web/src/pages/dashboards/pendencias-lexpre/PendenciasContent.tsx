import type { CSSProperties } from 'react'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { BarList } from '../../../components/charts/BarList.tsx'
import { GaugeChart } from '../../../components/charts/GaugeChart.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat, MiniStat, Pill, StackedRate } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { seriesByYear, topN } from '../../../lib/charts.ts'
import { fmt } from '../../../lib/format.ts'
import type { PendenciasResponse } from '../../../types/index.ts'
import type { ContentProps } from '../types.ts'
import { CORES_ANO, MESES, diaCurto, diaLongo, mesNome, periodo } from '../setor/datas.ts'
import { CardDuplo, RitmoDosDois } from '../setor/IndicadoresCards.tsx'
import { ReajuizamentoResumo } from '../setor/Reajuizamento.tsx'
import { filaTone, isPlaceholder, mesParcial, share } from '../setor/setor.ts'
import { EquipePanel } from './EquipePanel.tsx'

// Metas da v1 (Pendências). Meta diária de resolvidas por pessoa (a linha "Meta: 6" do gráfico por funcionário);
// taxa de resolvidos mínima e cancelamento máximo (as faixas da comissão e dos medidores "Taxas do período").
const META_DIARIA_V1 = 6
const META_TAXA_RESOLVIDOS = 85
const MAX_TAXA_CANCELADAS = 5

// Pendências (LexPre): as métricas da v1 no layout novo (o mesmo do Protocolo, Peticionamento e Org. Documentos).
// As Pendências do banco legado (NG, RJ e LA) usam esta mesma página (pendencias/PendenciasLegadoContent.tsx).
// Carregar, erros, cabeçalho, período e filtros ficam no DashboardView.
export function PendenciasContent({ data, filters = {}, onToggleFilter }: ContentProps<PendenciasResponse>) {
    const s = data.stats
    // Reajuizamento: o LexPre ainda não registra (0, como na v1); o banco legado da NG/RJ tem; o da LA não
    // separa (os campos não vêm e os dois cards somem).
    const lexpre = data.meta.source === 'LexPre'
    // Pendências LexPre com o legado da unidade somado (NG/RJ/LA).
    const comLegado = data.fonte_indicadores === 'legado' || data.fonte_indicadores === 'misto'
    // Reajuizamento no LexPre: demandas.reajuizamento, fora dos totais e da comissão (+ o do legado, se houver).
    const origemReaj = comLegado ? ' (LexPre + banco legado)' : ''
    const comReaj = lexpre || s.pendencias_nao_resolvidas_reajuizamento !== undefined
    const porFuncionario =
        onToggleFilter && ((name: string) => void (!isPlaceholder(name) && onToggleFilter('funcionario', name)))

    const taxaResolvidos = s.pendencias_taxa_resolvidos
    const taxaNaoResolvidos = s.pendencias_taxa_nao_resolvidos
    const taxaCanceladas = s.pendencias_taxa_canceladas
    const naoResolvidasTone = filaTone(taxaNaoResolvidos)
    const resolvidosOk = taxaResolvidos >= META_TAXA_RESOLVIDOS
    const canceladasOk = taxaCanceladas <= MAX_TAXA_CANCELADAS
    const origens = topN(data.pendencias_nao_resolvidas_por_origem)
    const origemPrincipal = origens[0]?.name ?? null

    const pessoas = data.media_pendencias_resolvidas_por_funcionario
    const metaDiaria = META_DIARIA_V1 * Math.max(1, pessoas.length) // meta do setor = meta por pessoa x equipe

    const anos = seriesByYear(data.pendencias_resolvidas_por_mes ?? [])
    const ultimo = anos.length - 1
    const parcial = ultimo >= 0 ? mesParcial(anos[ultimo].year) : null
    // Mês a mês num card mais estreito: meses abreviados, para caber um rótulo (e o número) em cada mês.
    const mesesCurtos = MESES.map((m) => m.slice(0, 3))

    return (
        <div className="dsecs">
            <DashSection
                index={1}
                eyebrow="Visão geral"
                title="Indicadores do período"
                subtitle={
                    data.fonte_indicadores === 'legado'
                        ? 'Sem pendências no LexPre neste período: números das Pendências do banco legado.'
                        : data.fonte_indicadores === 'misto'
                          ? 'Somam LexPre + Pendências do banco legado (volume, fila, taxas e tempos). Comparativos são do LexPre.'
                          : 'Volume e status das pendências no intervalo selecionado (quando aplicável).'
                }
            >
                <div className="grid grid-stat">
                    <HeroStat
                        label="Total de pendências"
                        icon="alert"
                        tone="accent"
                        value={<CountUp value={s.pendencias_total} format={fmt.int} />}
                        hint="Pendências que entraram no setor no período: resolvidas, não resolvidas e canceladas."
                        footer={
                            <>
                                <FootRow
                                    left={
                                        <span>
                                            Resolvidas:{' '}
                                            <strong className="num">
                                                <CountUp value={s.pendencias_resolvidas} format={fmt.int} />
                                            </strong>{' '}
                                            <span className="tone-text-ok">({fmt.dec1(taxaResolvidos)}%)</span>
                                        </span>
                                    }
                                />
                                <span className="progress" aria-hidden="true">
                                    <span style={{ '--w': `${Math.min(100, taxaResolvidos)}%` } as CSSProperties} />
                                </span>
                            </>
                        }
                    />
                    <HeroStat
                        label="Não resolvidas"
                        icon="x-circle"
                        tone="danger"
                        value={<CountUp value={s.pendencias_nao_resolvidas} format={fmt.int} />}
                        below={
                            <StackedRate
                                text={`${fmt.dec1(taxaNaoResolvidos)}%`}
                                caption="do total"
                                tone={naoResolvidasTone}
                            />
                        }
                        hint="Pendências em aberto no setor agora. Não depende do período."
                        footer={
                            <FootRow
                                left="Origem principal"
                                right={origemPrincipal && <span className="tone-text-accent">{origemPrincipal}</span>}
                            />
                        }
                    />
                    <HeroStat
                        label="Resolvidas"
                        icon="check-circle"
                        tone="ok"
                        value={<CountUp value={s.pendencias_resolvidas} format={fmt.int} />}
                        below={<DeltaPill value={s.comparativo_pendencias_resolvidas} suffix="vs mês anterior" plain />}
                        hint="Pendências resolvidas no período."
                        footer={
                            <FootRow
                                left={
                                    <span className={resolvidosOk ? 'tone-text-ok' : 'tone-text-warn'}>
                                        Taxa: {fmt.dec1(taxaResolvidos)}%
                                    </span>
                                }
                                right={<span className="num">meta {fmt.int(META_TAXA_RESOLVIDOS)}%</span>}
                            />
                        }
                    />
                    <CardDuplo
                        label="Tempo de resolução"
                        icon="clock"
                        tone="info"
                        hint="Da entrada da pendência à resolução, nas resolvidas no período. Média e mediana (metade levou até este tempo), com a variação vs mês anterior."
                        caixas={[
                            {
                                label: 'Média',
                                value: <CountUp value={s.media_tempo_resolvidos_pendencia} format={fmt.duracao} />,
                                delta: s.comparativo_tempo_medio_resolvidos_pendencia,
                                betterWhenDown: true,
                            },
                            {
                                label: 'Mediana',
                                value: <CountUp value={s.mediana_tempo_resolvidos_pendencia} format={fmt.duracao} />,
                                delta: s.comparativo_mediana_tempo_resolvidos_pendencia ?? null,
                                betterWhenDown: true,
                            },
                        ]}
                        footer={
                            <FootRow
                                left={
                                    s.comparativo_tempo_medio_resolvidos_pendencia === null && !lexpre ? (
                                        'Da entrada à resolução'
                                    ) : (
                                        <RitmoDosDois
                                            media={s.comparativo_tempo_medio_resolvidos_pendencia}
                                            mediana={s.comparativo_mediana_tempo_resolvidos_pendencia ?? null}
                                        />
                                    )
                                }
                                right={<span className="num muted">{data.meta.unit}</span>}
                            />
                        }
                    />
                </div>
                {/* 3 cards (com atraso, canceladas, triagem) + o de reajuizamento quando a página o tem. */}
                <div className={`grid ${comReaj ? 'grid-stat' : 'grid-stat-3'} grid-mini grid-mini-stack`}>
                    <MiniStat
                        label="Não resolvidas há mais de 5 dias"
                        icon="clock"
                        tone="warn"
                        value={<CountUp value={s.pendencias_nao_resolvidas_com_atraso} format={fmt.int} />}
                        below={
                            <StackedRate
                                text={`${fmt.dec1(share(s.pendencias_nao_resolvidas_com_atraso, s.pendencias_nao_resolvidas))}%`}
                                caption="das não resolvidas"
                                tone="warn"
                            />
                        }
                        hint="Pendências em aberto cuja entrada foi há mais de 5 dias. Não depende do período."
                    />
                    <MiniStat
                        label="Canceladas"
                        icon="x-circle"
                        tone="neutral"
                        value={<CountUp value={s.pendencias_canceladas} format={fmt.int} />}
                        below={
                            <StackedRate
                                text={`${fmt.dec1(taxaCanceladas)}%`}
                                caption={`do total · máx. ${fmt.int(MAX_TAXA_CANCELADAS)}%`}
                                tone={canceladasOk ? 'ok' : 'danger'}
                            />
                        }
                        hint="Pendências canceladas no período."
                    />
                    <MiniStat
                        label="Triagem"
                        icon="sheet"
                        tone="info"
                        value={<CountUp value={s.pendencias_triagem} format={fmt.int} />}
                        below={<StackedRate text="—" caption="aguardando triagem" tone="neutral" />}
                        hint="Demandas na Triagem agora (antes de virar pendência). Não depende do período."
                    />
                    {comReaj && (
                        <ReajuizamentoResumo
                            setor="Pendências"
                            periodo={{
                                label: 'Resolvidas',
                                value: s.pendencias_resolvidas_reajuizamento,
                                hint: lexpre
                                    ? `Resolvidas: pendências de reajuizamento resolvidas no período${origemReaj}.`
                                    : 'Resolvidas: pendências de reajuizamento abertas no período e já resolvidas.',
                            }}
                            fila={{
                                label: 'Não resolvidas',
                                value: s.pendencias_nao_resolvidas_reajuizamento,
                                // No legado (página antiga) é do período: abertas no período e ainda não resolvidas.
                                quando: lexpre ? 'agora' : 'período',
                                hint: lexpre
                                    ? `Não resolvidas: pendências de reajuizamento em aberto agora${origemReaj}.`
                                    : 'Não resolvidas: pendências de reajuizamento abertas no período e ainda não resolvidas.',
                            }}
                        />
                    )}
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Indicadores"
                title="Taxas do período"
                subtitle="Resolvidos, não resolvidos e canceladas em relação ao total de pendências abertas no período."
            >
                <div className="grid taxas-grid">
                    <ChartCard
                        title="Taxa de resolvidos"
                        action={
                            <Pill tone={resolvidosOk ? 'ok' : 'warn'}>
                                {resolvidosOk ? 'Na meta' : 'Abaixo da meta'}
                            </Pill>
                        }
                    >
                        <GaugeChart
                            value={taxaResolvidos}
                            color={resolvidosOk ? 'var(--ok-dot)' : 'var(--chart-1)'}
                            marker={META_TAXA_RESOLVIDOS}
                            caption={`Meta: ${fmt.dec1(META_TAXA_RESOLVIDOS)}%`}
                        />
                    </ChartCard>
                    <ChartCard
                        title="Taxa de não resolvidos"
                        action={<Pill tone={naoResolvidasTone}>{fmt.int(s.pendencias_nao_resolvidas)} em aberto</Pill>}
                    >
                        <GaugeChart value={taxaNaoResolvidos} color="var(--chart-1)" caption="do total" />
                    </ChartCard>
                    <ChartCard
                        title="Taxa de canceladas"
                        action={
                            <Pill tone={canceladasOk ? 'ok' : 'danger'}>
                                {canceladasOk ? 'Dentro do limite' : 'Acima do limite'}
                            </Pill>
                        }
                    >
                        <GaugeChart
                            value={taxaCanceladas}
                            color={canceladasOk ? 'var(--ok-dot)' : 'var(--c-danger)'}
                            marker={MAX_TAXA_CANCELADAS}
                            caption={`Máx. ${fmt.int(MAX_TAXA_CANCELADAS)}%`}
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Produtividade"
                title="Produção diária e desempenho por funcionário"
                subtitle="Série diária de resoluções e desempenho médio da equipe no período."
            >
                <div className="grid dist-grid">
                    <ChartCard
                        title="Produção diária – Pendências"
                        subtitle={`${periodo(data.meta.from, data.meta.to)} • Passe o cursor sobre os dias para detalhes`}
                        action={
                            <Pill tone="ok">
                                <span className="legend-dash" aria-hidden="true" /> Meta diária: {fmt.int(metaDiaria)}
                            </Pill>
                        }
                    >
                        <LineChart
                            height={340}
                            area
                            labels={data.pendencias_resolvidas_por_dia.map((p) => diaCurto(p.name))}
                            reference={{ value: metaDiaria, label: `Meta: ${fmt.int(metaDiaria)}/dia` }}
                            tooltip={{
                                heading: 'Dia',
                                title: (i) => diaLongo(data.pendencias_resolvidas_por_dia[i]?.name),
                            }}
                            series={[
                                {
                                    label: 'Resolvidas',
                                    color: 'var(--chart-1)',
                                    values: data.pendencias_resolvidas_por_dia.map((p) => p.value),
                                },
                            ]}
                        />
                    </ChartCard>
                    <ChartCard title="Desempenho por funcionário">
                        <EquipePanel
                            media={pessoas}
                            comissao={data.comissionamento_pendencias_por_funcionario ?? []}
                            meta={META_DIARIA_V1}
                            metaTaxa={META_TAXA_RESOLVIDOS}
                            maxCancelamento={MAX_TAXA_CANCELADAS}
                            filteredTo={filters.funcionario ?? []}
                            onFilterPerson={porFuncionario}
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={4}
                eyebrow="Análises"
                title="Origem e evolução mensal"
                subtitle="Distribuição do backlog por setor de origem e série de resolvidas mês a mês."
            >
                <div className="grid origem-grid">
                    <ChartCard
                        title="Origem das não resolvidas"
                        action={<Pill tone={naoResolvidasTone}>{fmt.int(s.pendencias_nao_resolvidas)} em aberto</Pill>}
                        footer={
                            origemPrincipal && (
                                <FootRow
                                    left="Principal origem:"
                                    right={<strong className="tone-text-accent">{origemPrincipal}</strong>}
                                />
                            )
                        }
                    >
                        <BarList items={origens} total={s.pendencias_nao_resolvidas} showShare wrapNames />
                    </ChartCard>
                    <ChartCard
                        title="Resolvidas mês a mês"
                        subtitle={comLegado ? 'LexPre + banco legado, somados mês a mês' : undefined}
                        tag={<Pill>Série Anual (Jan – Dez)</Pill>}
                    >
                        <LineChart
                            height={320}
                            legend
                            emphasizeData
                            labels={mesesCurtos}
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
                </div>
            </DashSection>
        </div>
    )
}
