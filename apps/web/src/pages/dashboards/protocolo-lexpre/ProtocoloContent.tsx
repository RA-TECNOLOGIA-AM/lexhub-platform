import type { CSSProperties } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { ColumnChart } from '../../../components/charts/ColumnChart.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat, MiniStat, Pill, ToneIcon } from '../../../components/dashboard/StatCard.tsx'
import { deltaTone } from '../../../components/dashboard/tone.ts'
import { parseMonth, seriesByYear, sortByMonth, topN } from '../../../lib/charts.ts'
import { fmt } from '../../../lib/format.ts'
import type { ProtocoloResponse } from '../../../types/index.ts'
import type { ContentProps } from '../types.ts'
import { FuncionarioPanel } from './FuncionarioPanel.tsx'
import { devolucoes, funcionarios, isPlaceholder, leituraDevolucao, mesParcial, share } from './charts.ts'

// Meta diária de protocolos por funcionário da v1 (a linha "Meta: 20"). A V2 manda `metas` quando
// a regra for definida; até lá, vale a da v1.
const META_POR_FUNCIONARIO_V1 = 20

const MESES = [
    'janeiro',
    'fevereiro',
    'março',
    'abril',
    'maio',
    'junho',
    'julho',
    'agosto',
    'setembro',
    'outubro',
    'novembro',
    'dezembro',
]
const MES_CURTO = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
// Uma cor por ano; o ano mais recente fica sempre com a cor principal.
const CORES_ANO = ['var(--chart-1)', 'var(--chart-3)', 'var(--chart-4)', 'var(--chart-5)']

// O Protocolo (LexPre): as métricas da v1 no layout novo. Carregar, erros, cabeçalho, período e
// filtros ficam no DashboardView; clicar numa matéria ou num funcionário liga o filtro.
export function ProtocoloContent({ data, filters = {}, onToggleFilter }: ContentProps<ProtocoloResponse>) {
    const s = data.stats
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
    // Fila pequena é saudável; acima de 5% pede atenção e acima de 15%, ação.
    const filaTone = fila < 5 ? 'ok' : fila < 15 ? 'warn' : 'danger'
    const topRepresado = topN(data.represados_por_materia, 1)[0]?.name ?? null

    const pessoas = funcionarios(data)
    const meta = data.metas?.protocolados_por_funcionario ?? META_POR_FUNCIONARIO_V1
    // Meta do setor por dia = meta por pessoa x quem protocolou no período.
    const produtores = Math.max(1, data.media_protocolados_por_funcionario.length)
    const metaDiaria = meta * produtores

    const top10 = topN(data.protocolados_por_materia)
    const top10Soma = top10.reduce((sum, p) => sum + p.value, 0)
    const dev = devolucoes(s)

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
                subtitle="Protocolados, represados, valores e tempos no intervalo selecionado (quando aplicável)."
            >
                <div className="grid grid-stat">
                    <HeroStat
                        label="Protocolados"
                        icon="check-circle"
                        tone="accent"
                        value={fmt.int(protocolados)}
                        aside={<DeltaPill value={s.protocolados_total.comparativo} />}
                        hint="Demandas que saíram do Protocolo como protocoladas (Aguardando Despacho Inicial) no período."
                        footer={
                            <>
                                <FootRow
                                    left={<span className="tone-text-ok">{fmt.dec1(eficiencia)}% eficiência</span>}
                                    right={<span className="num">{fmt.dec1(eficiencia)}%</span>}
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
                        value={fmt.int(s.represados)}
                        aside={<Pill tone="warn">{fmt.dec1(fila)}% fila</Pill>}
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
                        value={fmt.brl(s.valor_causa_protocolado.total)}
                        below={<DeltaPill value={s.valor_causa_protocolado.comparativo} suffix=" vs mês anterior" />}
                        hint="Soma do valor de causa das demandas protocoladas no período."
                        footer={
                            <FootRow
                                left="Volume financeiro acumulado"
                                right={<span className="num tone-text-ok">{unit}</span>}
                            />
                        }
                    />
                    <HeroStat
                        label="Média de tempo protocolado"
                        icon="clock"
                        tone="info"
                        value={fmt.duracao(s.media_tempo_protocolado)}
                        aside={<DeltaPill value={s.comparativo_tempo_medio_protocolado} betterWhenDown />}
                        hint="Tempo médio entre a entrada no Protocolo e o protocolo, nas demandas protocoladas no período."
                        footer={
                            <FootRow
                                left={<Velocidade value={s.comparativo_tempo_medio_protocolado} />}
                                right="vs mês anterior"
                            />
                        }
                    />
                </div>
                <div className="grid grid-stat grid-mini">
                    <MiniStat
                        label="Protocolados de reajuizamento"
                        icon="check-circle"
                        tone="neutral"
                        value={fmt.int(0)}
                        extra={<span className="muted small">no período</span>}
                        hint="O LexPre ainda não registra reajuizamento: fica 0, como na v1."
                    />
                    <MiniStat
                        label="Represados de reajuizamento"
                        icon="x-circle"
                        tone="neutral"
                        value={fmt.int(0)}
                        extra={<span className="muted small">no período</span>}
                        hint="O LexPre ainda não registra reajuizamento: fica 0, como na v1."
                    />
                    <MiniStat
                        label="Ticket médio protocolado"
                        icon="dollar"
                        tone="ok"
                        value={fmt.brl(s.ticket_medio_protocolado.total)}
                        extra={<DeltaPill value={s.ticket_medio_protocolado.comparativo} plain />}
                        hint="Valor de causa protocolado dividido pela quantidade de protocolados no período."
                    />
                    <MiniStat
                        label="Mediana de tempo protocolado"
                        icon="clock"
                        tone="info"
                        value={fmt.duracao(s.mediana_tempo_protocolado)}
                        extra={<DeltaPill value={s.comparativo_mediana_tempo_protocolado} betterWhenDown plain />}
                        hint="Metade das demandas protocoladas no período levou até este tempo no Protocolo."
                    />
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Devolução"
                title="Devolvido para outros setores"
                subtitle="Demandas devolvidas do Protocolo — valores sempre totais, independentes do período selecionado."
            >
                <div className="card dev-sum">
                    <ToneIcon icon="undo" tone="accent" />
                    <div className="dev-sum-text">
                        <span className="dev-sum-title">
                            <span className="hero-l">Total de devoluções ativas:</span>
                            <strong className="num">{fmt.int(dev.total)}</strong>
                            <Pill>Escopo global (independe do filtro de data)</Pill>
                        </span>
                        <span className="muted small">
                            Distribuição proporcional entre Peticionamento ({fmt.dec1(dev.partes[0].pct)}%), Organização
                            Documental ({fmt.dec1(dev.partes[1].pct)}%) e Pendência ({fmt.dec1(dev.partes[2].pct)}%).
                        </span>
                    </div>
                    {dev.total > 0 && (
                        <div className="dev-bar">
                            <div className="dev-bar-labels num">
                                {dev.partes
                                    .filter((p) => p.value > 0)
                                    .map((p) => (
                                        <span key={p.key} className={`dev-${p.key}`}>
                                            {p.label}: {fmt.dec1(p.pct)}%
                                        </span>
                                    ))}
                            </div>
                            <div className="split" aria-hidden="true">
                                {dev.partes.map((p) => (
                                    <span key={p.key} className={`dev-${p.key}`} style={{ flexGrow: p.value }} />
                                ))}
                            </div>
                        </div>
                    )}
                </div>
                <div className="grid grid-stat-3">
                    {devCards.map((c) => {
                        const leitura = leituraDevolucao(c.value, c.comparativo)
                        return (
                            <HeroStat
                                key={c.label}
                                label={c.label}
                                icon="x-circle"
                                tone={c.value === 0 ? 'neutral' : deltaTone(c.comparativo, true)}
                                outline
                                value={fmt.int(c.value)}
                                aside={<DeltaPill value={c.comparativo} betterWhenDown />}
                                hint={`Demandas que o Protocolo devolveu para ${c.setor} (total histórico).`}
                                footer={
                                    <FootRow
                                        left={<span className={`tone-text-${leitura.tone}`}>{leitura.text}</span>}
                                        right="vs mês anterior"
                                    />
                                }
                            />
                        )
                    })}
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
                            represadoMateria={topRepresado}
                            filteredTo={filters.funcionario ?? []}
                            onFilterPerson={porFuncionario}
                            onFilterMateria={porMateria}
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
                subtitle="Comparativo ano a ano de protocolos totais."
            >
                <ChartCard title="Protocolados mês a mês" tag={<Pill>Série Anual (Jan – Dez)</Pill>}>
                    <LineChart
                        height={340}
                        legend
                        area={anos.length === 1}
                        emphasizeData
                        labels={MESES}
                        partial={parcial !== null ? { series: ultimo, index: parcial } : undefined}
                        tooltip={{ heading: 'Mês', title: (i) => MESES[i][0].toUpperCase() + MESES[i].slice(1) }}
                        series={anos.map((a, i) => ({
                            label: String(a.year),
                            color: CORES_ANO[(anos.length - 1 - i) % CORES_ANO.length],
                            values: a.values,
                        }))}
                    />
                </ChartCard>
            </DashSection>
        </div>
    )
}

// "Ganho de velocidade" quando o tempo caiu; "Perda" quando subiu.
function Velocidade({ value }: { value: number | null }) {
    if (!value) return <span className="muted">Sem variação</span>
    return value < 0 ? (
        <span className="tone-text-ok">Ganho de velocidade</span>
    ) : (
        <span className="tone-text-danger">Perda de velocidade</span>
    )
}

// '2026-11-03' -> '03/11' (o ano já está no Período).
function diaCurto(iso: string): string {
    const m = /^\d{4}-(\d{2})-(\d{2})$/.exec(iso)
    return m ? `${m[2]}/${m[1]}` : iso
}

// '2026-11-03' -> '03/11/2026' (caixa do cursor).
function diaLongo(iso: string | undefined): string {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso ?? '')
    return m ? `${m[3]}/${m[2]}/${m[1]}` : (iso ?? '')
}

// '2026-11-04' a '2026-11-13' -> '04/11 a 13/11/2026'.
function periodo(from: string, to: string): string {
    if (!from || !to) return 'Período selecionado'
    const a = diaLongo(from)
    const b = diaLongo(to)
    return from.slice(0, 4) === to.slice(0, 4) ? `${a.slice(0, 5)} a ${b}` : `${a} a ${b}`
}

// 'nov 2026' -> 'Nov / 2026' (rótulo da barra).
function mesBarra(name: string): string {
    const m = parseMonth(name)
    return m ? `${MES_CURTO[m.month - 1]} / ${m.year}` : name
}
