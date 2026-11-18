import { useState } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { FootRow, HeroStat, Pill } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { DataTable } from '../../../components/ui/DataTable.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { pickSingle, toggleFilter } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import type { ContentProps } from '../types.ts'
import { Paginador } from '../execucao/partes.tsx'
import { tomStatus } from '../execucao/setorExecucao.ts'
import { usePagina } from '../execucao/usePagina.ts'
import { diaLongo } from '../setor/datas.ts'
import {
    META_RESOLUCAO,
    duracaoHoras,
    lerPublicacoes,
    linhaDoTempo,
    resolucao,
    statusAgendamento,
    type Publicacao,
    type PublicacoesResponse,
} from './publicacoes.ts'

const valor = (v: number | null) => (v === null ? '—' : <CountUp value={v} format={fmt.int} />)
const CORES = ['var(--chart-1)', 'var(--chart-3)', 'var(--chart-4)', 'var(--danger)']

// Publicações (NG, LA e RJ): as seções da página da v1 (NG/PublicacoesNG.tsx) no layout da V2. Clicar nos gráficos
// filtra a página: leitor e matéria somam (vários), os outros trocam (um de cada), como na v1.
export function PublicacoesContent({ data, filters = {}, onFiltersChange }: ContentProps<PublicacoesResponse>) {
    const p = lerPublicacoes(data)
    const r = resolucao(p.recebidas ?? 0, p.cumpridas ?? 0)
    const linha = linhaDoTempo(data, data.meta.from ?? '', data.meta.to ?? '')
    const set = onFiltersChange
    const alternar = set && ((key: keyof DashboardFilters, v: string) => set(toggleFilter(filters, key, v)))
    const escolher = set && ((key: keyof DashboardFilters, v: string) => set(pickSingle(filters, key, v)))
    const marcados = (key: keyof DashboardFilters) => filters[key] ?? []
    const diaRef = p.diaReferencia ? diaLongo(p.diaReferencia) : '—'
    const barras = (
        titulo: string,
        itens: { name: string; value: number }[],
        key: keyof DashboardFilters,
        varios = false,
    ) => (
        <ChartCard
            className="ex-rolagem"
            title={titulo}
            subtitle={`Total ${fmt.int(itens.reduce((t, x) => t + x.value, 0))} · clique para filtrar`}
        >
            <BarList
                items={itens}
                showShare
                wrapNames
                selected={marcados(key)}
                onSelect={
                    (varios ? alternar : escolher) && ((v) => v !== '—' && (varios ? alternar : escolher)?.(key, v))
                }
                selectLabel={`Filtrar: ${titulo.toLowerCase()}`}
            />
        </ChartCard>
    )

    return (
        <div className="dsecs">
            <DashSection
                index={1}
                eyebrow="Visão geral"
                title="Indicadores do período"
                subtitle={`Recebidas, pendentes, cumpridas e tempos no intervalo selecionado · dia de referência (fim do período): ${diaRef}.`}
            >
                <div className="grid pb-ind">
                    <HeroStat
                        label="Recebidas no período"
                        icon="inbox"
                        tone="info"
                        value={valor(p.recebidas)}
                        hint="Publicações com DATA_DISPONIBILIZACAO no período."
                    />
                    <HeroStat
                        label="Pendentes"
                        icon="clock"
                        tone="warn"
                        value={valor(p.pendentes)}
                        hint="Estoque de agora: publicações com status Visualizado ou Não visualizado (não depende do período)."
                    />
                    <HeroStat
                        label="Recebidas hoje"
                        icon="calendar"
                        tone="neutral"
                        value={valor(p.recebidasHoje)}
                        hint="Publicações com data de disponibilização hoje (data do servidor), independente do período."
                    />
                    <HeroStat
                        className="pb-alto"
                        label="Zerado no período"
                        icon="target"
                        tone="ok"
                        value={valor(p.zeradas)}
                        hint="Quantas vezes o estoque de pendentes (reconstruído dia a dia: chegou e ainda não tinha sido cumprida) foi de mais que zero para zero no período. Dias seguidos zerados contam uma vez; respeita os filtros da página."
                        footer={<FootRow left="Estoque de pendentes" right={<Pill tone="ok">no período</Pill>} />}
                    />
                    <HeroStat
                        className="pb-alto"
                        label="Cumpridas no mesmo dia"
                        icon="check-circle"
                        tone="accent"
                        value={valor(p.mesmoDia)}
                        below={
                            p.pctMesmoDia !== null && (
                                <span className="muted small">
                                    <strong className="num">{fmt.pct2(p.pctMesmoDia)}</strong> das{' '}
                                    {fmt.int(p.recebidasDiaRef ?? 0)} chegadas em {diaRef}
                                </span>
                            )
                        }
                        hint={`Chegaram e foram cumpridas no mesmo dia, no dia de referência (${diaRef}). % = cumpridas no mesmo dia ÷ chegadas nesse dia. Em todo o histórico, com os mesmos filtros: ${fmt.int(p.mesmoDiaTotal ?? 0)} cumpridas no mesmo dia da chegada, de ${fmt.int(p.comDataDisponibilizacao ?? 0)} com data de disponibilização.`}
                        footer={<FootRow left="Dia de referência" right={<Pill tone="accent">{diaRef}</Pill>} />}
                    />
                    <HeroStat
                        label="Cumpridas no período"
                        icon="check-circle"
                        tone="ok"
                        value={valor(p.cumpridas)}
                        hint="Publicações com status Cumprido e DATA_CONCLUSAO no período."
                    />
                    <HeroStat
                        label="Tempo médio de tratamento"
                        icon="clock"
                        tone="info"
                        value={duracaoHoras((p.tempoMedioDias ?? 0) * 24)}
                        hint="Média entre a disponibilização e a conclusão das cumpridas no período."
                    />
                    <HeroStat
                        label="Cumpridas no dia de referência"
                        icon="check-circle"
                        tone="neutral"
                        value={valor(p.cumpridasDiaRef)}
                        hint={`Cumpridas com DATA_CONCLUSAO em ${diaRef} (o último dia do período; a v1 chamava de "Cumpridas hoje").`}
                    />
                </div>
                <div className="card pb-taxa ex-mt">
                    <div className="pb-taxa-topo">
                        <div>
                            <span className="pb-taxa-rot">Taxa de resolução — publicações no período</span>
                            <strong
                                className={`num pb-taxa-v ${!r.temDados ? 'muted' : r.comissiona ? 'tone-text-ok' : 'tone-text-danger'}`}
                            >
                                {r.temDados ? `${fmt.dec1(r.taxa)}%` : '–'}
                            </strong>
                            <span className="muted small">
                                {fmt.int(p.cumpridas ?? 0)} cumprida(s) de {fmt.int(p.recebidas ?? 0)} recebida(s) ·
                                mínimo para comissionar: <strong>{META_RESOLUCAO}%</strong>
                            </span>
                        </div>
                        <Pill tone={!r.temDados ? 'neutral' : r.comissiona ? 'ok' : 'danger'}>
                            {!r.temDados ? 'Sem dados' : r.comissiona ? 'Comissiona' : 'Não comissiona'}
                        </Pill>
                    </div>
                    <span className="pb-barra" aria-hidden="true">
                        <span className="ok" style={{ width: `${r.pctCumpridas}%` }} />
                        <span className="nao" style={{ width: `${r.pctNaoCumpridas}%` }} />
                        <i style={{ left: `${META_RESOLUCAO}%` }} />
                    </span>
                </div>
            </DashSection>

            {linha.temDados && (
                <DashSection
                    index={2}
                    eyebrow="Linha do tempo"
                    title="Publicações diárias"
                    subtitle="Chegadas, cumpridas e atraso ao longo dos dias do período."
                >
                    <ChartCard
                        title="Linha do tempo das publicações diárias"
                        subtitle='"Atraso em dias" (como a v1): nos dias que ainda têm pendente, quantos dias faz até o dia de referência.'
                    >
                        <LineChart
                            height={320}
                            legend
                            labels={linha.dias.map((d) => `${d.slice(8, 10)}/${d.slice(5, 7)}`)}
                            tooltip={{ heading: 'Dia', title: (i) => diaLongo(linha.dias[i]) }}
                            series={linha.series.map((s, i) => ({
                                label: s.label,
                                color: s.label === 'Atraso em dias' ? CORES[3] : CORES[i],
                                values: s.values,
                                dashed: s.label === 'Atraso em dias',
                            }))}
                        />
                    </ChartCard>
                </DashSection>
            )}

            <DashSection
                index={linha.temDados ? 3 : 2}
                eyebrow="Distribuição"
                title="Matérias, leitores e tribunais"
                subtitle="Publicações recebidas no período por dimensão e as demandas por leitor · clique nos gráficos para filtrar."
            >
                <div className="grid pb-dist">
                    <div className="pb-col">
                        {barras('Publicações por matéria', p.porMateria, 'materia_publicacoes', true)}
                        {barras('Publicações por tipo de documento', p.porDocumento, 'documento_publicacoes')}
                    </div>
                    <DemandasLeitores
                        itens={p.demandas}
                        selecionados={marcados('leitor_publicacoes')}
                        onSelect={alternar && ((v) => v !== '—' && alternar('leitor_publicacoes', v))}
                    />
                    <div className="pb-col">
                        <Tribunais
                            itens={p.porTribunal}
                            selecionados={marcados('tribunal_publicacoes')}
                            onSelect={escolher && ((v) => escolher('tribunal_publicacoes', v))}
                        />
                        {barras('Publicações por órgão/vara', p.porOrgao, 'orgao_publicacoes')}
                    </div>
                </div>
            </DashSection>

            <DashSection
                index={linha.temDados ? 4 : 3}
                eyebrow="Pós-finalização"
                title="Agendamento após a publicação finalizada"
                subtitle="Publicações cumpridas no período que geraram (ou não) um agendamento em qualquer setor, e qual."
            >
                <p className="pb-resumo">
                    <strong className="num">{fmt.int(p.agendamento.com)}</strong> com agendamento e{' '}
                    <strong className="num">{fmt.int(p.agendamento.sem)}</strong> sem agendamento
                    {p.agendamento.pct !== null && (
                        <>
                            {' '}
                            (<strong className="num">{fmt.dec1(p.agendamento.pct)}%</strong> tiveram agendamento)
                        </>
                    )}
                    .
                </p>
                <div className="grid tk-tres">
                    {barras('Por atividade', p.porAtividade, 'atividade_agendamento_publicacoes')}
                    {barras('Por setor', p.porSetor, 'setor_agendamento_publicacoes')}
                    <ChartCard title="Com x sem agendamento" subtitle="Clique numa fatia para filtrar">
                        <PieChart
                            items={[
                                { name: 'Com agendamento', value: p.agendamento.com, color: 'var(--chart-1)' },
                                { name: 'Sem agendamento', value: p.agendamento.sem, color: 'var(--chart-3)' },
                            ]}
                            sort={false}
                            size={220}
                            labels
                            labelsTwoLines
                            legendWhenNarrow
                            selected={marcados('status_agendamento_publicacoes').map((v) =>
                                v === 'sem' ? 'Sem agendamento' : 'Com agendamento',
                            )}
                            onSelect={
                                escolher && ((v) => escolher('status_agendamento_publicacoes', statusAgendamento(v)))
                            }
                            selectLabel="Filtrar"
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={linha.temDados ? 5 : 4}
                eyebrow="Lista"
                title="Lista de publicações"
                subtitle={
                    p.unidade === 'LA'
                        ? 'Publicações recebidas no período, uma por linha.'
                        : 'Publicações recebidas no período, uma por linha. Setor / atividade: o agendamento mais recente criado depois da conclusão e como ele está.'
                }
            >
                <ListaPublicacoes
                    itens={p.lista}
                    setorLabel={p.unidade === 'LA' ? 'Tribunal / órgão' : 'Setor / atividade'}
                />
            </DashSection>
        </div>
    )
}

type Modo = 'compacta' | 'expandida'
type Ordem = 'recente' | 'antiga' | 'id'

// A lista de publicações da v1 (10 por página), em modo compacto (abre assim) ou expandido.
function ListaPublicacoes({ itens, setorLabel }: { itens: Publicacao[]; setorLabel: string }) {
    const [modo, setModo] = useState<Modo>('compacta')
    const [ordem, setOrdem] = useState<Ordem>('recente')
    const ordenados = [...itens].sort((a, b) => {
        if (ordem === 'id') return Number(a.id) - Number(b.id)
        const x = a.recebidaEm ?? ''
        const y = b.recebidaEm ?? ''
        return ordem === 'recente' ? y.localeCompare(x) : x.localeCompare(y)
    })
    const pag = usePagina(ordenados, 10)
    const compacta = modo === 'compacta'
    return (
        <ChartCard
            title="Publicações"
            subtitle={`${fmt.int(itens.length)} publicação(ões)`}
            action={
                <div className="ex-acoes">
                    <Segmented
                        label="Ordem"
                        options={[
                            { value: 'recente', label: 'Mais recentes' },
                            { value: 'antiga', label: 'Mais antigas' },
                            { value: 'id', label: 'Por nº' },
                        ]}
                        value={ordem}
                        onChange={setOrdem}
                    />
                    <Segmented
                        label="Modo da lista"
                        options={[
                            { value: 'compacta', label: 'Compacta' },
                            { value: 'expandida', label: 'Expandida' },
                        ]}
                        value={modo}
                        onChange={setModo}
                    />
                </div>
            }
        >
            <div className={compacta ? 'ex-lista compacta' : 'ex-lista'}>
                <DataTable
                    rows={pag.itens}
                    rowKey={(x) => x.id}
                    empty="Nenhuma publicação no período."
                    columns={[
                        { header: '#', render: (x) => <span className="num muted">{x.id}</span> },
                        {
                            header: 'Publicação',
                            render: (x) =>
                                compacta ? (
                                    <span className="ex-corta" title={`${x.documento} · ${x.materia}`}>
                                        {x.documento || '—'}
                                    </span>
                                ) : (
                                    <span className="ex-tarefa">
                                        <strong>{x.documento || '—'}</strong>
                                        <span className="tone-text-accent small">{x.materia}</span>
                                    </span>
                                ),
                        },
                        { header: 'Status', render: (x) => <Pill tone={tomStatus(x.status)}>{x.status}</Pill> },
                        { header: 'Leitor', render: (x) => x.leitor || '—' },
                        {
                            header: setorLabel,
                            render: (x) => (
                                <span className={compacta ? 'ex-corta' : undefined} title={x.setor}>
                                    {x.setor || '—'}
                                </span>
                            ),
                        },
                        {
                            header: 'Recebida em',
                            render: (x) => (
                                <span className="num">{x.recebidaEm ? diaLongo(x.recebidaEm.slice(0, 10)) : '—'}</span>
                            ),
                        },
                    ]}
                />
            </div>
            <Paginador pagina={pag.pagina} total={pag.total} onChange={pag.setPagina} />
        </ChartCard>
    )
}

// "Demandas por funcionário": um cartão por leitor, com o total, a barra (cumpridas no período + pendentes de agora)
// e os dois números embaixo. Clicar filtra a página pelo leitor.
function DemandasLeitores({
    itens,
    selecionados,
    onSelect,
}: {
    itens: { name: string; cumpridas: number; pendentes: number; total: number }[]
    selecionados: string[]
    onSelect?: (nome: string) => void
}) {
    const maior = Math.max(...itens.map((d) => d.total), 1)
    return (
        <ChartCard
            className="pb-demandas"
            title="Demandas por funcionário"
            subtitle="Distribuição entre demandas cumpridas no período e estoque pendente atual por leitor."
            action={onSelect && <span className="muted small">Clique para filtrar</span>}
        >
            <div className="pb-legenda">
                <span>
                    <i className="pb-cump" /> Cumpridas no período
                </span>
                <span>
                    <i className="pb-pend" /> Pendentes (estoque atual)
                </span>
            </div>
            {itens.length === 0 ? (
                <ChartEmpty>Nenhum dado disponível.</ChartEmpty>
            ) : (
                <ul className="pb-leitores" role="list">
                    {itens.map((d) => {
                        const marcado = selecionados.includes(d.name)
                        return (
                            <li key={d.name} className={selecionados.length > 0 && !marcado ? 'dim' : undefined}>
                                <button
                                    type="button"
                                    disabled={!onSelect}
                                    aria-pressed={marcado}
                                    onClick={() => onSelect?.(d.name)}
                                    title={`${d.name}: ${fmt.int(d.cumpridas)} cumpridas, ${fmt.int(d.pendentes)} pendentes`}
                                >
                                    <span className="pb-leitor-topo">
                                        <strong>{d.name}</strong>
                                        <strong className="num">{fmt.int(d.total)}</strong>
                                    </span>
                                    <span className="pb-leitor-barra" aria-hidden="true">
                                        <span
                                            className="pb-cump"
                                            style={{ width: `${(d.cumpridas / maior) * 100}%` }}
                                        />
                                        <span
                                            className="pb-pend"
                                            style={{ width: `${(d.pendentes / maior) * 100}%` }}
                                        />
                                    </span>
                                    <span className="pb-leitor-pe">
                                        <span>
                                            <i className="pb-cump" /> Cumpridas:{' '}
                                            <strong className="num">{fmt.int(d.cumpridas)}</strong>
                                        </span>
                                        <span>
                                            <i className="pb-pend" /> Pendentes:{' '}
                                            <strong className="num tone-text-info">{fmt.int(d.pendentes)}</strong>
                                        </span>
                                    </span>
                                </button>
                            </li>
                        )
                    })}
                </ul>
            )}
        </ChartCard>
    )
}

// "Publicações por tribunal": a rosca com o total no meio e a lista ao lado (nome, quantidade e %), as duas
// clicáveis; passar o cursor numa linha destaca a fatia.
function Tribunais({
    itens,
    selecionados,
    onSelect,
}: {
    itens: { name: string; value: number }[]
    selecionados: string[]
    onSelect?: (nome: string) => void
}) {
    const [hover, setHover] = useState<string | null>(null)
    const total = itens.reduce((t, x) => t + x.value, 0)
    const cor = (i: number) => `var(--pie-${(i % 10) + 1})`
    return (
        <ChartCard
            title="Publicações por tribunal"
            subtitle="Clique numa fatia ou item para filtrar"
            tag={
                <Pill tone="accent">
                    {fmt.int(itens.length)} tribuna{itens.length === 1 ? 'l' : 'is'}
                </Pill>
            }
        >
            {itens.length === 0 ? (
                <ChartEmpty>Nenhum dado disponível.</ChartEmpty>
            ) : (
                <div className="pb-tribunais">
                    <PieChart
                        items={itens.map((x, i) => ({ ...x, color: cor(i) }))}
                        sort={false}
                        size={190}
                        selected={selecionados}
                        onSelect={onSelect}
                        selectLabel="Filtrar pelo tribunal"
                        hover={hover}
                        onHover={setHover}
                    />
                    <ul className="pb-trib-lista" role="list">
                        {itens.map((x, i) => {
                            const marcado = selecionados.includes(x.name)
                            return (
                                <li key={x.name} className={selecionados.length > 0 && !marcado ? 'dim' : undefined}>
                                    <button
                                        type="button"
                                        disabled={!onSelect}
                                        aria-pressed={marcado}
                                        onClick={() => onSelect?.(x.name)}
                                        onMouseEnter={() => setHover(x.name)}
                                        onMouseLeave={() => setHover(null)}
                                        onFocus={() => setHover(x.name)}
                                        onBlur={() => setHover(null)}
                                    >
                                        <i style={{ background: cor(i) }} />
                                        <span className="pb-trib-nome">{x.name}</span>
                                        <span className="num">
                                            <strong>{fmt.int(x.value)}</strong>{' '}
                                            <span className="muted">
                                                ({fmt.dec1(total ? (x.value / total) * 100 : 0)}%)
                                            </span>
                                        </span>
                                    </button>
                                </li>
                            )
                        })}
                    </ul>
                </div>
            )}
        </ChartCard>
    )
}
