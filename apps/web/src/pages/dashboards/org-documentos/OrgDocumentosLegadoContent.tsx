import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { ColumnChart } from '../../../components/charts/ColumnChart.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat, MiniStat, Pill, StackedRate } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { seriesByYear, sortByMonth, topN } from '../../../lib/charts.ts'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { CORES_ANO, MESES, diaCurto, diaLongo, mesBarra, mesNome, periodo } from '../setor/datas.ts'
import { DevolucaoCard, DevolucaoResumo, Velocidade } from '../setor/Devolucao.tsx'
import { FuncionarioPanel, type PainelLabels } from '../setor/FuncionarioPanel.tsx'
import {
    META_POR_FUNCIONARIO_V1,
    devolucoes,
    filaTone as tomDaFila,
    funcionarios,
    isPlaceholder,
    mesParcial,
    share,
} from '../setor/setor.ts'
import { lerOrgDocumentos } from './orgDocumentos.ts'

const VS = ' vs mês anterior'

const PAINEL: PainelLabels = {
    setor: 'Org. de Documentos',
    feitos: 'Resolvidos',
    pendentes: 'Represados',
    alerta: 'represados',
    media: 'Média diária',
    valor: 'Valor de causa',
}

// Número que pode faltar na resposta ('—'), com a contagem animada quando vem.
const valor = (v: number | null, format: (n: number) => string) =>
    v === null ? '—' : <CountUp value={v} format={format} />

// A Organização de Documentos do banco legado (NG e RJ), com as seções da página da v1 no layout da
// Organização de Documentos (LexPre). Carregar, erros, cabeçalho, período e filtros ficam no DashboardView;
// clicar numa matéria ou num funcionário liga o filtro.
export function OrgDocumentosLegadoContent({ data, filters = {}, onToggleFilter }: ContentProps<V1GenericoResponse>) {
    const p = lerOrgDocumentos(data)
    const unit = data.meta.unit
    // Linha "Sem matéria"/"Sem funcionário" (e "-", a matéria vazia da v1) não vira filtro.
    const pick = (key: 'materia' | 'funcionario') =>
        onToggleFilter &&
        ((name: string) => void (!isPlaceholder(name) && name.trim() !== '-' && onToggleFilter(key, name)))
    const porMateria = pick('materia')
    const porFuncionario = pick('funcionario')

    const resolvidos = p.resolvidos ?? 0
    const represados = p.represados ?? 0
    const fila = share(represados, resolvidos + represados)
    const filaTone = tomDaFila(fila)
    const topRepresado = topN(p.naoPorMateria, 1)[0]?.name ?? null
    const top10 = topN(p.porMateria)
    const top10Soma = top10.reduce((sum, m) => sum + m.value, 0)
    const pessoas = funcionarios({
        feitos: p.porFuncionario,
        pendentes: p.naoPorFuncionario,
        media: p.mediaPorFuncionario,
        valor: p.valorPorFuncionario,
    })
    const meta = META_POR_FUNCIONARIO_V1
    // Meta diária do setor: 20 por dia, fixa (não multiplica por quem resolveu no período).
    const metaDiaria = meta
    // Na LA não há a seção de devolução (só o retorno para Pendência, que fica nos cards): as seguintes sobem.
    const salto = p.la ? 1 : 0
    const dev = devolucoes([
        { key: 'pendencia', label: 'Pendência', value: p.retornoPendencia ?? 0 },
        { key: 'peticionamento', label: 'Confecção', value: p.retornoConfeccao ?? 0 },
    ])

    const anos = seriesByYear(p.porMes)
    const ultimo = anos.length - 1
    const parcial = ultimo >= 0 ? mesParcial(anos[ultimo].year) : null
    const represadosMes = sortByMonth(p.naoPorMes)

    return (
        <div className="dsecs">
            <DashSection
                index={1}
                eyebrow="Visão geral"
                title="Indicadores do período"
                subtitle="Resoluções e tempos no intervalo selecionado, com comparativo ao período anterior."
            >
                <div className="grid grid-stat">
                    <HeroStat
                        label="Total resolvidos"
                        icon="check-circle"
                        tone="accent"
                        value={valor(p.resolvidos, fmt.int)}
                        below={<DeltaPill value={p.comparativo.resolvidos} suffix={VS} plain />}
                        hint="Processos que saíram da Organização de Documentos no período: manuais + automáticos."
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
                        label="Represados"
                        icon="x-circle"
                        tone="danger"
                        value={valor(p.represados, fmt.int)}
                        below={<StackedRate text={`${fmt.dec1(fila)}%`} caption="na fila" tone={filaTone} />}
                        hint="Processos no setor ainda sem organização: a fila de agora. Não depende do período."
                        footer={
                            <FootRow
                                left="Aguardando organização"
                                right={topRepresado && <span className="num tone-text-accent">{topRepresado}</span>}
                            />
                        }
                    />
                    <HeroStat
                        label="Tempo médio resolvidos"
                        icon="clock"
                        tone="info"
                        value={valor(p.mediaTempo, fmt.duracao)}
                        below={<DeltaPill value={p.comparativo.mediaTempo} betterWhenDown suffix={VS} plain />}
                        hint="Tempo médio entre a entrada no setor e a saída, nos processos resolvidos no período."
                        footer={
                            <FootRow
                                left={
                                    p.comparativo.mediaTempo === null ? (
                                        'Da entrada à saída do setor'
                                    ) : (
                                        <Velocidade value={p.comparativo.mediaTempo} />
                                    )
                                }
                            />
                        }
                    />
                    <HeroStat
                        label="Mediana de tempo resolvidos"
                        icon="clock"
                        tone="info"
                        value={valor(p.medianaTempo, fmt.duracao)}
                        hint="Metade dos processos resolvidos no período levou até este tempo no setor."
                        footer={<FootRow left="Metade levou até este tempo" />}
                    />
                </div>
                <div className="grid grid-stat grid-mini grid-mini-stack">
                    <MiniStat
                        label="Resolvido manualmente"
                        icon="users"
                        tone="accent"
                        value={valor(p.manuais, fmt.int)}
                        below={<DeltaPill value={p.comparativo.manuais} suffix={VS} plain />}
                        hint="Organizados por um funcionário. Base da comissão."
                    />
                    <MiniStat
                        label="Resolvido automaticamente"
                        icon="flow"
                        tone="info"
                        value={valor(p.automaticos, fmt.int)}
                        below={<DeltaPill value={p.comparativo.automaticos} suffix={VS} plain />}
                        hint="Organizados e peticionados pelo sistema (automático ligado)."
                    />
                    {p.reajuizamento !== null && (
                        <MiniStat
                            label="Resolvidos reajuizamento"
                            icon="check-circle"
                            tone="neutral"
                            value={valor(p.reajuizamento, fmt.int)}
                            below={<DeltaPill value={p.comparativo.reajuizamento} suffix={VS} plain />}
                            hint="Processos de reajuizamento resolvidos no período."
                        />
                    )}
                    <MiniStat
                        label="Cancelados"
                        icon="x-circle"
                        tone="neutral"
                        value={valor(p.cancelados, fmt.int)}
                        below={<DeltaPill value={p.comparativo.cancelados} betterWhenDown suffix={VS} plain />}
                        hint="Processos cancelados que saíram da Organização de Documentos no período."
                    />
                    {p.la && (
                        <MiniStat
                            label="Retorno Pendência"
                            icon="undo"
                            tone="danger"
                            value={valor(p.retornoPendencia, fmt.int)}
                            below={<StackedRate text="acumulado" caption="não depende do período" tone="neutral" />}
                            hint="Processos que a Organização de Documentos devolveu para Pendências (total acumulado). Na LA é o único retorno."
                        />
                    )}
                </div>
            </DashSection>

            {!p.la && (
                <DashSection
                    index={2}
                    eyebrow="Devolução"
                    title="Devolvido para outros setores"
                    subtitle="Processos que voltaram para Pendência e para a Confecção — valores acumulados, independentes do período selecionado."
                >
                    <DevolucaoResumo dev={dev} />
                    <div className="grid dev-grid">
                        <DevolucaoCard
                            label="Retorno Pendência"
                            value={p.retornoPendencia ?? 0}
                            comparativo={null}
                            hint="Processos que a Organização de Documentos devolveu para Pendências (total acumulado)."
                        />
                        <DevolucaoCard
                            label="Retorno Confecção"
                            value={p.retornoConfeccao ?? 0}
                            comparativo={null}
                            hint="Processos que a Organização de Documentos devolveu para a Confecção (Peticionamento), total acumulado."
                        />
                    </div>
                </DashSection>
            )}

            <DashSection
                index={3 - salto}
                eyebrow="Distribuições"
                title="Por matéria e por funcionário"
                subtitle="Clique em qualquer matéria à esquerda para aplicar filtro cruzado nos demais indicadores e na curva diária."
            >
                <div className="grid dist-grid">
                    <ChartCard
                        title="Top 10 – Resolvidos por matéria"
                        subtitle={`Representatividade sobre os ${fmt.int(resolvidos)} resolvidos do período`}
                        action={porMateria && <Pill tone="accent">Clique para filtrar</Pill>}
                        footer={
                            top10.length > 0 && (
                                <FootRow
                                    left={
                                        <>
                                            Top 10 soma <strong className="num">{fmt.int(top10Soma)}</strong> resolvidos
                                            ({fmt.dec1(share(top10Soma, resolvidos))}% do total)
                                        </>
                                    }
                                    right={`Demais matérias: ${fmt.int(Math.max(0, resolvidos - top10Soma))}`}
                                />
                            )
                        }
                    >
                        <BarList
                            items={top10}
                            total={resolvidos || undefined}
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
                index={4 - salto}
                eyebrow="Produtividade"
                title="Produção diária e represados mensais"
                subtitle="Evolução de volumes resolvidos por dia e acumulado de não resolvidos por mês."
            >
                <div className="grid prod-grid">
                    <ChartCard
                        title="Produção diária – Organização de documentos"
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
                                    label: 'Resolvidos',
                                    color: 'var(--chart-1)',
                                    values: p.porDia.map((d) => d.value),
                                },
                            ]}
                        />
                    </ChartCard>
                    <ChartCard
                        title="Não resolvidos mês a mês"
                        action={<Pill tone={filaTone}>Retenção: {fmt.dec1(fila)}%</Pill>}
                        footer={
                            <div className="fstack">
                                <FootRow
                                    left="Taxa de retenção atual:"
                                    right={
                                        <span className="num">
                                            <strong className={`tone-text-${filaTone}`}>{fmt.dec1(fila)}%</strong>{' '}
                                            <span className="muted">
                                                ({fmt.int(represados)} de {fmt.int(resolvidos + represados)})
                                            </span>
                                        </span>
                                    }
                                />
                                <div className="fbox fbox-row small">
                                    <span className="muted">
                                        {p.naoPorMateria.length === 1 ? 'Pendência única:' : 'Principal pendência:'}
                                    </span>
                                    <strong className="num tone-text-accent">{topRepresado ?? 'Nenhuma'}</strong>
                                </div>
                            </div>
                        }
                    >
                        <ColumnChart
                            height={260}
                            className="col-accent"
                            caption="Mês"
                            categories={represadosMes.map((m) => mesBarra(m.name))}
                            series={[
                                {
                                    label: 'Não resolvidos',
                                    color: 'var(--chart-1)',
                                    values: represadosMes.map((m) => m.value),
                                },
                            ]}
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={5 - salto}
                eyebrow="Evolução"
                title="Organizados mês a mês"
                subtitle="Comparado por ano; não depende do período."
            >
                <ChartCard
                    title="Organizados mês a mês"
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
