import { useState, type CSSProperties } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { ColumnChart } from '../../../components/charts/ColumnChart.tsx'
import { DonutChart } from '../../../components/charts/DonutChart.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat, MiniStat, Pill, StackedRate } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { seriesByYear, sortByMonth, topN } from '../../../lib/charts.ts'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import { CORES_ANO, MESES, diaCurto, diaLongo, mesBarra, mesNome, periodo } from '../setor/datas.ts'
import { DevolucaoCard, DevolucaoResumo, Velocidade } from '../setor/Devolucao.tsx'
import { FuncionarioPanel, type PainelLabels } from '../setor/FuncionarioPanel.tsx'
import { RubricasModal } from '../setor/RubricasModal.tsx'
import {
    META_POR_FUNCIONARIO_V1,
    devolucoes,
    filaTone as tomDaFila,
    funcionarios,
    isPlaceholder,
    mesParcial,
    share,
} from '../setor/setor.ts'
import type { PeticionamentoLexpreResponse } from './types.ts'

const PAINEL: PainelLabels = {
    setor: 'Peticionamento',
    feitos: 'Peticionados',
    pendentes: 'Não peticionados',
    alerta: 'não peticionados',
    media: 'Média diária',
    valor: 'Valor confeccionado',
    valorSecundario: 'Valor protocolado',
    valorRestante: 'Falta protocolar',
}

type MateriaVista = 'peticionados' | 'protocolados'

// O Peticionamento (LexPre): as métricas da v1 no layout novo (o mesmo do Protocolo). Carregar, erros,
// cabeçalho, período e filtros ficam no DashboardView; clicar numa matéria ou num funcionário liga o filtro.
export function PeticionamentoLexpreContent({
    data,
    filters = {},
    onToggleFilter,
}: ContentProps<PeticionamentoLexpreResponse>) {
    const [vista, setVista] = useState<MateriaVista>('peticionados')
    const [pacote, setPacote] = useState<string | null>(null) // matéria reunida com o modal aberto
    const s = data.stats
    const unit = data.meta.unit
    // Linha "Sem matéria"/"Sem funcionário" não vira filtro (a API não teria o que procurar).
    const pick = (key: 'materia' | 'funcionario') =>
        onToggleFilter && ((name: string) => void (!isPlaceholder(name) && onToggleFilter(key, name)))
    const filtrarMateria = pick('materia')
    // Pacotes (rubrica reunida): clicar abre o modal com as rubricas de cada demanda, como na v1.
    const reunidas = data.rubricas_reunidas ?? []
    const pacotes = reunidas.map((r) => r.materia)
    const porMateria =
        filtrarMateria && ((name: string) => (pacotes.includes(name) ? setPacote(name) : filtrarMateria(name)))
    const aberto = reunidas.find((r) => r.materia === pacote)
    const porFuncionario = pick('funcionario')

    const peticionados = s.total_peticionados.total
    const protocolados = s.protocolados_total.total
    const operacao = peticionados + s.represados // resolvidos no período + fila do setor (a "Taxa de resolvidos")
    const fila = share(s.represados, operacao)
    const filaTone = tomDaFila(fila)
    const topRepresado = topN(data.represados_por_materia, 1)[0]?.name ?? null

    const pessoas = funcionarios({
        feitos: data.peticionados_por_funcionario,
        pendentes: data.represados_por_funcionario,
        media: data.media_peticionado_por_funcionario,
        valor: data.valor_causa_por_funcionario,
        valorSecundario: data.valor_causa_protocolado_por_funcionario,
    })
    const meta = META_POR_FUNCIONARIO_V1
    // Meta do setor por dia = meta por pessoa x quem peticionou no período.
    const metaDiaria = meta * Math.max(1, data.media_peticionado_por_funcionario.length)

    const materias = vista === 'peticionados' ? data.peticionados_por_materia : data.protocolados_por_materia
    const totalVista = vista === 'peticionados' ? peticionados : protocolados
    const top10 = topN(materias)
    const top10Soma = top10.reduce((sum, p) => sum + p.value, 0)
    const dev = devolucoes([
        { key: 'org_doc', label: 'Org Doc', value: s.retorno_org_doc },
        { key: 'pendencia', label: 'Pendência', value: s.retorno_pendencia },
    ])

    const naoPeticionadosMes = sortByMonth(data.represados_por_mes)
    const anos = seriesByYear(data.peticionados_por_mes)
    const ultimo = anos.length - 1
    const parcial = ultimo >= 0 ? mesParcial(anos[ultimo].year) : null

    return (
        <div className="dsecs">
            <DashSection
                index={1}
                eyebrow="Visão geral"
                title="Indicadores do período"
                subtitle={
                    data.fonte_indicadores === 'legado'
                        ? 'Sem peticionados no LexPre neste período: números do Peticionamento legado (volume, fila, tempos e valores). Devoluções continuam do LexPre.'
                        : data.fonte_indicadores === 'misto'
                          ? 'Volume, valor e tempos somam LexPre + Peticionamento legado no período. Fila, cancelados e devoluções são do LexPre.'
                          : 'Volume, tempos, valores e fila de não peticionados no intervalo selecionado.'
                }
            >
                <div className="grid grid-stat">
                    <HeroStat
                        label="Total peticionados"
                        icon="check-circle"
                        tone="accent"
                        value={<CountUp value={peticionados} format={fmt.int} />}
                        below={<DeltaPill value={s.total_peticionados.comparativo} suffix=" vs mês anterior" plain />}
                        hint="Demandas confeccionadas (não canceladas) que saíram do Peticionamento no período: manuais + automáticas."
                        footer={
                            <>
                                <FootRow
                                    left={
                                        <span>
                                            Protocolados:{' '}
                                            <strong className="num">
                                                <CountUp value={protocolados} format={fmt.int} />
                                            </strong>{' '}
                                            <span className="tone-text-ok">
                                                ({fmt.dec1(share(protocolados, peticionados))}%)
                                            </span>
                                        </span>
                                    }
                                />
                                <span className="progress" aria-hidden="true">
                                    <span
                                        style={
                                            {
                                                '--w': `${Math.min(100, share(protocolados, peticionados))}%`,
                                            } as CSSProperties
                                        }
                                    />
                                </span>
                            </>
                        }
                    />
                    <HeroStat
                        label="Não peticionados"
                        icon="x-circle"
                        tone="danger"
                        value={<CountUp value={s.represados} format={fmt.int} />}
                        below={<StackedRate text={`${fmt.dec1(fila)}%`} caption="na fila" tone={filaTone} />}
                        hint="Demandas no Peticionamento agora, ainda sem confecção. Não depende do período."
                        footer={
                            <FootRow
                                left="Aguardando peticionamento"
                                right={topRepresado && <span className="num tone-text-accent">{topRepresado}</span>}
                            />
                        }
                    />
                    <HeroStat
                        label="Valor confeccionado"
                        icon="dollar"
                        tone="ok"
                        value={<CountUp value={s.valor_causa_confeccionado.total} format={fmt.brl} />}
                        below={
                            <DeltaPill
                                value={s.valor_causa_confeccionado.comparativo}
                                suffix=" vs mês anterior"
                                plain
                            />
                        }
                        hint="Soma do valor de causa das demandas confeccionadas no período (ANP usa o dano moral)."
                        footer={
                            <FootRow
                                left="Volume financeiro confeccionado"
                                right={<span className="num tone-text-ok">{unit}</span>}
                            />
                        }
                    />
                    <HeroStat
                        label="Tempo médio peticionado"
                        icon="clock"
                        tone="info"
                        value={<CountUp value={s.media_tempo_peticionado} format={fmt.duracao} />}
                        below={
                            <DeltaPill
                                value={s.comparativo_tempo_medio_peticionado}
                                betterWhenDown
                                suffix=" vs mês anterior"
                                plain
                            />
                        }
                        hint="Tempo médio entre a entrada no Peticionamento e a saída, nas demandas confeccionadas no período."
                        footer={<FootRow left={<Velocidade value={s.comparativo_tempo_medio_peticionado} />} />}
                    />
                </div>
                <div className="grid grid-mini-5 grid-mini grid-mini-stack">
                    <MiniStat
                        label="Peticionados manualmente"
                        icon="users"
                        tone="accent"
                        value={<CountUp value={s.peticionados_manualmente.total} format={fmt.int} />}
                        below={
                            <DeltaPill value={s.peticionados_manualmente.comparativo} suffix=" vs mês anterior" plain />
                        }
                        hint="Confeccionadas por um funcionário (peticionamento automático desligado). Base da comissão."
                    />
                    <MiniStat
                        label="Peticionados automaticamente"
                        icon="flow"
                        tone="info"
                        value={<CountUp value={s.peticionados_automaticamente.total} format={fmt.int} />}
                        below={
                            <DeltaPill
                                value={s.peticionados_automaticamente.comparativo}
                                suffix=" vs mês anterior"
                                plain
                            />
                        }
                        hint="Peticionadas pelo sistema (peticionamento automático ligado)."
                    />
                    {data.fonte_indicadores === 'legado' && s.processos_em_revisao != null ? (
                        <MiniStat
                            label="Revisão"
                            icon="eye"
                            tone="warn"
                            value={<CountUp value={s.processos_em_revisao} format={fmt.int} />}
                            below={<StackedRate text="agora" caption="não depende do período" tone="neutral" />}
                            hint="Processos em revisão (STATUS = REVISÃO): a conferência antes do protocolo. Total de agora no legado, como na página antiga."
                        />
                    ) : (
                        <MiniStat
                            label="Cancelados"
                            icon="x-circle"
                            tone="neutral"
                            value={<CountUp value={s.cancelados.total} format={fmt.int} />}
                            below={
                                <DeltaPill
                                    value={s.cancelados.comparativo}
                                    betterWhenDown
                                    suffix=" vs mês anterior"
                                    plain
                                />
                            }
                            hint="Demandas canceladas que saíram do Peticionamento no período."
                        />
                    )}
                    <MiniStat
                        label="Ticket médio"
                        icon="dollar"
                        tone="ok"
                        value={<CountUp value={s.ticket_medio_confeccionado.total} format={fmt.brl} />}
                        below={
                            <DeltaPill
                                value={s.ticket_medio_confeccionado.comparativo}
                                suffix=" vs mês anterior"
                                plain
                            />
                        }
                        hint="Valor confeccionado dividido pelo total de peticionados no período."
                    />
                    <MiniStat
                        label="Mediana de tempo peticionado"
                        icon="clock"
                        tone="info"
                        value={<CountUp value={s.mediana_tempo_peticionado} format={fmt.duracao} />}
                        below={
                            <DeltaPill
                                value={s.comparativo_mediana_tempo_peticionado}
                                betterWhenDown
                                suffix=" vs mês anterior"
                                plain
                            />
                        }
                        hint="Metade das demandas confeccionadas no período levou até este tempo no Peticionamento."
                    />
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Devolução"
                title="Devolvido para outros setores"
                subtitle="Demandas devolvidas do Peticionamento — valores sempre totais, independentes do período selecionado."
            >
                <DevolucaoResumo dev={dev} />
                <div className="grid dev-grid">
                    <div className="dev-cards">
                        <DevolucaoCard
                            label="Devolvido p/ Org Doc"
                            value={s.retorno_org_doc}
                            comparativo={s.comparativo_retorno_org_doc}
                            hint="Demandas que o Peticionamento devolveu para a Organização de Documentos (total histórico)."
                        />
                        <DevolucaoCard
                            label="Devolvido p/ Pendência"
                            value={s.retorno_pendencia}
                            comparativo={s.comparativo_retorno_pendencia}
                            hint="Demandas que o Peticionamento devolveu para Pendências (total histórico)."
                        />
                    </div>
                    <ChartCard
                        title="Taxa de resolvidos"
                        subtitle="Peticionados no período × não peticionados agora"
                        action={<Pill tone={filaTone}>{fmt.dec1(share(peticionados, operacao))}% resolvidos</Pill>}
                    >
                        <DonutChart
                            slices={[
                                { label: 'Resolvidos', value: peticionados, color: 'var(--ok-dot)' },
                                { label: 'Não resolvidos', value: s.represados, color: 'var(--chart-1)' },
                            ]}
                        />
                    </ChartCard>
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
                        title={`Top 10 – ${vista === 'peticionados' ? 'Peticionados' : 'Protocolados'} por matéria`}
                        subtitle={`Representatividade sobre os ${fmt.int(totalVista)} ${vista} do período`}
                        action={
                            <Segmented
                                label="Contar por"
                                value={vista}
                                onChange={setVista}
                                options={[
                                    { value: 'peticionados', label: 'Peticionados' },
                                    { value: 'protocolados', label: 'Protocolados' },
                                ]}
                            />
                        }
                        footer={
                            top10.length > 0 && (
                                <FootRow
                                    left={
                                        <>
                                            Top 10 soma <strong className="num">{fmt.int(top10Soma)}</strong> {vista} (
                                            {fmt.dec1(share(top10Soma, totalVista))}% do total)
                                        </>
                                    }
                                    right={`Demais matérias: ${fmt.int(Math.max(0, totalVista - top10Soma))}`}
                                />
                            )
                        }
                    >
                        <BarList
                            items={top10}
                            total={totalVista}
                            showShare
                            selected={filters.materia}
                            onSelect={porMateria}
                            selectLabel="Filtrar pela matéria"
                            stacked={pacotes}
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
                title="Produção diária e não peticionados por mês"
                subtitle="Evolução de volumes peticionados por dia e acumulado de não peticionados por mês de entrada."
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
                            labels={data.peticionados_por_dia.map((p) => diaCurto(p.name))}
                            reference={{ value: metaDiaria, label: `Meta: ${fmt.int(metaDiaria)}/dia` }}
                            tooltip={{ heading: 'Dia', title: (i) => diaLongo(data.peticionados_por_dia[i]?.name) }}
                            series={[
                                {
                                    label: 'Peticionados',
                                    color: 'var(--chart-1)',
                                    values: data.peticionados_por_dia.map((p) => p.value),
                                },
                            ]}
                        />
                    </ChartCard>
                    <ChartCard
                        title="Não peticionados por mês"
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
                            categories={naoPeticionadosMes.map((p) => mesBarra(p.name))}
                            series={[
                                {
                                    label: 'Não peticionados',
                                    color: 'var(--chart-1)',
                                    values: naoPeticionadosMes.map((p) => p.value),
                                },
                            ]}
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={5}
                eyebrow="Evolução"
                title="Peticionados mês a mês"
                subtitle="Comparado por ano; meses anteriores ao LexPre vêm do Peticionamento legado."
            >
                <ChartCard
                    title="Peticionados mês a mês"
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
            {aberto && (
                <RubricasModal
                    materia={aberto.materia}
                    demandas={aberto.demandas}
                    filtered={filters.materia?.includes(aberto.materia) ?? false}
                    onToggleFilter={filtrarMateria && (() => filtrarMateria(aberto.materia))}
                    onClose={() => setPacote(null)}
                />
            )}
        </div>
    )
}
