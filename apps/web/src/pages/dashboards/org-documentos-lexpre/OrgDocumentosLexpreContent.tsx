import { useState, type CSSProperties } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { ColumnChart } from '../../../components/charts/ColumnChart.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat, MiniStat, Pill, StackedRate } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { seriesByYear, sortByMonth, topN } from '../../../lib/charts.ts'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import { CORES_ANO, MESES, diaCurto, diaLongo, mesBarra, mesNome, periodo } from '../setor/datas.ts'
import { Velocidade } from '../setor/Devolucao.tsx'
import { FuncionarioPanel, type PainelLabels } from '../setor/FuncionarioPanel.tsx'
import { RubricasModal } from '../setor/RubricasModal.tsx'
import {
    META_POR_FUNCIONARIO_V1,
    filaTone as tomDaFila,
    funcionarios,
    isPlaceholder,
    mesParcial,
    share,
} from '../setor/setor.ts'
import type { OrgDocumentosLexpreResponse } from './types.ts'

const PAINEL: PainelLabels = {
    setor: 'Org. de Documentos',
    feitos: 'Resolvidos',
    pendentes: 'Represados',
    alerta: 'represados',
    media: 'Média diária',
    valor: 'Valor de causa',
    valorSecundario: 'Valor protocolado',
    valorRestante: 'Falta protocolar',
}

type MateriaVista = 'setor' | 'protocolados'

// A Organização de documentos (LexPre): as métricas da v1 no layout novo (o mesmo do Protocolo e do
// Peticionamento). Carregar, erros, cabeçalho, período e filtros ficam no DashboardView.
export function OrgDocumentosLexpreContent({
    data,
    filters = {},
    onToggleFilter,
}: ContentProps<OrgDocumentosLexpreResponse>) {
    const [vista, setVista] = useState<MateriaVista>('setor')
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

    const resolvidos = s.resolvidos_total.total
    const protocolados = s.protocolados_total.total
    const operacao = resolvidos + s.represados // resolvidos no período + fila do setor (a "Taxa de resolvidos")
    const fila = share(s.represados, operacao)
    const filaTone = tomDaFila(fila)
    const topRepresado = topN(data.nao_organizados_total_por_materia, 1)[0]?.name ?? null

    const pessoas = funcionarios({
        feitos: data.resolvidos_por_funcionario,
        pendentes: data.nao_organizados_por_funcionario,
        media: data.media_resolvidos_por_funcionario,
        valor: data.valor_causa_por_funcionario,
        valorSecundario: data.valor_causa_protocolado_por_funcionario,
    })
    const meta = META_POR_FUNCIONARIO_V1
    // Meta do setor por dia = meta por pessoa x quem resolveu no período.
    const metaDiaria = meta * Math.max(1, data.media_resolvidos_por_funcionario.length)

    const materias = vista === 'setor' ? data.resolvidos_total_por_materia : data.protocolados_total_por_materia
    const totalVista = vista === 'setor' ? resolvidos : protocolados
    const nomeVista = vista === 'setor' ? 'resolvidos' : 'protocolados'
    const top10 = topN(materias)
    const top10Soma = top10.reduce((sum, p) => sum + p.value, 0)

    const represadosMes = sortByMonth(data.nao_resolvidos_total_por_mes)
    const anos = seriesByYear(data.resolvidos_total_por_mes)
    const ultimo = anos.length - 1
    const parcial = ultimo >= 0 ? mesParcial(anos[ultimo].year) : null

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
                        value={<CountUp value={resolvidos} format={fmt.int} />}
                        below={<DeltaPill value={s.resolvidos_total.comparativo} suffix="vs mês anterior" plain />}
                        hint="Demandas que saíram da Organização de documentos no período: manuais + automáticas."
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
                                                ({fmt.dec1(share(protocolados, resolvidos))}%)
                                            </span>
                                        </span>
                                    }
                                />
                                <span className="progress" aria-hidden="true">
                                    <span
                                        style={
                                            {
                                                '--w': `${Math.min(100, share(protocolados, resolvidos))}%`,
                                            } as CSSProperties
                                        }
                                    />
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
                        hint="Demandas na Organização de documentos agora, ainda sem resolução. Não depende do período."
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
                        value={<CountUp value={s.media_tempo_resolvidos} format={fmt.duracao} />}
                        below={
                            <DeltaPill
                                value={s.comparativo_tempo_medio_resolvidos}
                                betterWhenDown
                                suffix="vs mês anterior"
                                plain
                            />
                        }
                        hint="Tempo médio entre a entrada no setor e a saída, nas demandas resolvidas no período."
                        footer={<FootRow left={<Velocidade value={s.comparativo_tempo_medio_resolvidos} />} />}
                    />
                    <HeroStat
                        label="Mediana de tempo resolvidos"
                        icon="clock"
                        tone="info"
                        value={<CountUp value={s.mediana_tempo_resolvidos} format={fmt.duracao} />}
                        below={
                            <DeltaPill
                                value={s.comparativo_mediana_tempo_resolvidos}
                                betterWhenDown
                                suffix="vs mês anterior"
                                plain
                            />
                        }
                        hint="Metade das demandas resolvidas no período levou até este tempo no setor."
                        footer={<FootRow left={<Velocidade value={s.comparativo_mediana_tempo_resolvidos} />} />}
                    />
                </div>
                <div className="grid grid-stat grid-mini grid-mini-stack">
                    <MiniStat
                        label="Resolvido manualmente"
                        icon="users"
                        tone="accent"
                        value={<CountUp value={s.organizados_manualmente.total} format={fmt.int} />}
                        below={
                            <DeltaPill value={s.organizados_manualmente.comparativo} suffix="vs mês anterior" plain />
                        }
                        hint="Organizadas por um funcionário. Base da comissão."
                    />
                    <MiniStat
                        label="Resolvido automaticamente"
                        icon="flow"
                        tone="info"
                        value={<CountUp value={s.organizados_e_peticionados_automaticamente.total} format={fmt.int} />}
                        below={
                            <DeltaPill
                                value={s.organizados_e_peticionados_automaticamente.comparativo}
                                suffix="vs mês anterior"
                                plain
                            />
                        }
                        hint="Organizadas e peticionadas pelo sistema (automático ligado)."
                    />
                    <MiniStat
                        label="Cancelados"
                        icon="x-circle"
                        tone="neutral"
                        value={<CountUp value={s.cancelados.total} format={fmt.int} />}
                        below={
                            <DeltaPill value={s.cancelados.comparativo} betterWhenDown suffix="vs mês anterior" plain />
                        }
                        hint="Demandas canceladas que saíram da Organização de documentos no período."
                    />
                    <MiniStat
                        label="Devolvido p/ Pendência"
                        icon="undo"
                        tone="danger"
                        value={<CountUp value={s.devolvido_pendencia} format={fmt.int} />}
                        below={
                            <DeltaPill
                                value={s.comparativo_devolvido_pendencia}
                                betterWhenDown
                                suffix="vs mês anterior"
                                plain
                            />
                        }
                        hint="Demandas que a Organização de documentos devolveu para Pendências (total histórico; o comparativo é das devoluções no período)."
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
                        title={`Top 10 – ${vista === 'setor' ? 'Resolvidos' : 'Protocolados'} por matéria`}
                        subtitle={`Representatividade sobre os ${fmt.int(totalVista)} ${nomeVista} do período`}
                        action={
                            <Segmented
                                label="Contar por"
                                value={vista}
                                onChange={setVista}
                                options={[
                                    { value: 'setor', label: 'No setor' },
                                    { value: 'protocolados', label: 'Protocolados' },
                                ]}
                            />
                        }
                        footer={
                            top10.length > 0 && (
                                <FootRow
                                    left={
                                        <>
                                            Top 10 soma <strong className="num">{fmt.int(top10Soma)}</strong>{' '}
                                            {nomeVista} ({fmt.dec1(share(top10Soma, totalVista))}% do total)
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
                index={3}
                eyebrow="Produtividade"
                title="Produção diária e represados mensais"
                subtitle="Evolução de volumes resolvidos por dia e acumulado de represados por mês de entrada."
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
                            labels={data.resolvidos_por_dia_org.map((p) => diaCurto(p.name))}
                            reference={{ value: metaDiaria, label: `Meta: ${fmt.int(metaDiaria)}/dia` }}
                            tooltip={{ heading: 'Dia', title: (i) => diaLongo(data.resolvidos_por_dia_org[i]?.name) }}
                            series={[
                                {
                                    label: 'Resolvidos',
                                    color: 'var(--chart-1)',
                                    values: data.resolvidos_por_dia_org.map((p) => p.value),
                                },
                            ]}
                        />
                    </ChartCard>
                    <ChartCard
                        title="Represados por mês de entrada"
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
                                        {data.nao_organizados_total_por_materia.length === 1
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
                            categories={represadosMes.map((p) => mesBarra(p.name))}
                            series={[
                                {
                                    label: 'Represados',
                                    color: 'var(--chart-1)',
                                    values: represadosMes.map((p) => p.value),
                                },
                            ]}
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={4}
                eyebrow="Evolução"
                title="Resolvidos mês a mês"
                subtitle="Comparativo ano a ano de resoluções totais."
            >
                <ChartCard title="Resolvidos mês a mês" tag={<Pill>Série Anual (Jan – Dez)</Pill>}>
                    <LineChart
                        height={340}
                        legend
                        area={anos.length === 1}
                        emphasizeData
                        labels={MESES}
                        partial={parcial !== null ? { series: ultimo, index: parcial } : undefined}
                        tooltip={{ heading: 'Mês', title: mesNome }}
                        series={anos.map((a, i) => ({
                            label: String(a.year),
                            color: CORES_ANO[(anos.length - 1 - i) % CORES_ANO.length],
                            values: a.values,
                        }))}
                    />
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
