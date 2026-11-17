import { useState } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { ColumnChart } from '../../../components/charts/ColumnChart.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { StackedBars } from '../../../components/charts/StackedBars.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat, MiniStat, Pill } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { DataTable } from '../../../components/ui/DataTable.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Modal } from '../../../components/ui/Modal.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { clearFilter, pickSingle, toggleFilter } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import type { ContentProps } from '../types.ts'
import { CardFiltro, Paginador } from '../execucao/partes.tsx'
import { numeroCnj } from '../execucao/setorExecucao.ts'
import { usePagina } from '../execucao/usePagina.ts'
import { CORES_ANO, MESES, diaLongo, mesNome } from '../setor/datas.ts'
import {
    alvaras,
    alvarasPorDia,
    alvarasPorMes,
    confeccao,
    diasUteisAte,
    distribuicoes,
    escopoDe,
    indicadores,
    lados,
    previsaoCompensacao,
    series,
    type Alvara,
    type AlvaraDia,
    type Comarca,
    type EstrategicoResponse,
    type Fluxo,
    type TarefaCS,
    type TaxaAtualizacao,
} from './estrategico.ts'

const VS = ' vs mês anterior'
const MES_ABREV = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
const MES_CURTO = MESES.map((m) => m[0].toUpperCase() + m.slice(1, 3))
const valor = (v: number, format: (n: number) => string) => <CountUp value={v} format={format} />
const taxaTexto = (t: number | null) => (t === null ? '—' : `${fmt.dec2(t)}%`)
const dias = (d: number) => `${fmt.dec1(d)} dias`
const hojeIso = () => new Date().toISOString().slice(0, 10)

// Linhas por ano (Jan–Dez): os anteriores tracejados e o mais recente cheio, como os "mês a mês" da V2.
function PorAno({
    mapa,
    format,
    height = 300,
}: {
    mapa: Map<string, (number | null)[]>
    format: (v: number) => string
    height?: number
}) {
    const anos = [...mapa.keys()]
    if (anos.length === 0) return <ChartEmpty>Sem dados no histórico.</ChartEmpty>
    return (
        <LineChart
            height={height}
            legend
            emphasizeData
            format={format}
            labels={MESES}
            tooltip={{ heading: 'Mês', title: mesNome }}
            series={anos.map((ano, i) => ({
                label: ano,
                color: CORES_ANO[(anos.length - 1 - i) % CORES_ANO.length],
                values: mapa.get(ano) ?? [],
                dashed: i < anos.length - 1,
                area: i === anos.length - 1,
            }))}
        />
    )
}

// A Execução Estratégico Geral (NG, LA e RJ), com as seções da página da v1 (NG/ExecucaoEstrategicoGeral.tsx) no layout da
// V2: Condenação e Acordos somados conforme o escopo (filtro Ambos / Condenação / Acordos).
export function EstrategicoContent({ data, filters = {}, onFiltersChange }: ContentProps<EstrategicoResponse>) {
    const escopo = escopoDe(filters.escopo)
    const l = lados(data, escopo)
    const k = indicadores(l)
    const s = series(l)
    const dist = distribuicoes(l)
    const cs = confeccao(data)
    const alv = alvaras(l)
    const [taxaAberta, setTaxaAberta] = useState(false)
    const [ano, setAno] = useState<string | null>(null)
    const anoAtivo = ano !== null && s.anos.includes(ano) ? ano : (s.anos.at(-1) ?? null)
    const [modoMateria, setModoMateria] = useState<'total' | 'qtd_entrada' | 'valor_entrada'>('total')
    const [modoSubfase, setModoSubfase] = useState<'total' | 'entrada'>('total')
    const [modoComarca, setModoComarca] = useState<'total' | 'entrada' | 'saida'>('total')
    const [modoCxA, setModoCxA] = useState<'total' | 'entrada' | 'saida'>('total')
    const [listaCS, setListaCS] = useState<'abertas' | 'concluidas' | null>(null)

    const set = onFiltersChange
    const alternar = set && ((key: keyof DashboardFilters, v: string) => set(toggleFilter(filters, key, v)))
    const escolher = set && ((key: keyof DashboardFilters, v: string) => set(pickSingle(filters, key, v)))
    const sufixo =
        escopo === 'condenacao'
            ? 'somente Execução Condenação'
            : escopo === 'acordos'
              ? 'somente Execução Acordos'
              : 'soma de Execução Condenação e Execução Acordos'

    // Mês sem dado (ex.: os que ainda não chegaram no ano corrente) fica vazio, sem cair para zero.
    const doAno = (m: Map<string, (number | null)[]>) => (anoAtivo ? (m.get(anoAtivo) ?? []) : [])
    const fluxoDoAno = (chave: Fluxo) => MES_ABREV.map((mes) => s.fluxo.get(`${mes} ${anoAtivo}`)?.[chave] ?? null)
    const seletorAno = s.anos.length > 0 && (
        <label className="field-select">
            <span className="sr-only">Ano</span>
            <select value={anoAtivo ?? ''} onChange={(e) => setAno(e.target.value)}>
                {s.anos.map((a) => (
                    <option key={a} value={a}>
                        {a}
                    </option>
                ))}
            </select>
        </label>
    )
    const materias = dist.materia[modoMateria]
    const comarcas = dist.comarca[modoComarca]
    const selAtividade = filters.atividade_execucao ?? []

    return (
        <div className="dsecs">
            <DashSection
                index={1}
                eyebrow="Visão geral"
                title="Indicadores"
                subtitle={`Volume em execução, entradas, saídas e valores no intervalo selecionado — ${sufixo}.`}
            >
                <div className="grid ex-ind-topo">
                    <HeroStat
                        label="Total em execução"
                        icon="check-circle"
                        tone="accent"
                        value={valor(k.total, fmt.int)}
                        hint="Quantos processos estão hoje na Execução (Condenação + Acordos); não muda com o período."
                        footer={<FootRow left="Processos na fase de Execução" right={<Pill>agora</Pill>} />}
                    />
                    <HeroStat
                        label="Valor total em execução"
                        icon="dollar"
                        tone="ok"
                        value={valor(k.valorTotal, fmt.brl)}
                        hint="Quanto falta receber dos processos hoje na Execução (se já houve incontroverso, só o restante). Ticket = valor ÷ quantidade."
                        footer={
                            <FootRow
                                left="Ticket médio total"
                                right={<strong className="num">{fmt.brl(k.ticketTotal)}</strong>}
                            />
                        }
                    />
                </div>
                <div className="grid ex-ind">
                    <HeroStat
                        label="Quantidade de entrada na execução"
                        icon="check-circle"
                        tone="info"
                        value={valor(k.entradas, fmt.int)}
                        below={<DeltaPill value={k.compEntradas} suffix={VS} plain />}
                        hint="Processos que entraram na Execução no período: Condenação pela data de execução; Acordos pela data em que o acordo foi fechado."
                    />
                    <HeroStat
                        label="Valor remanescente"
                        icon="dollar"
                        tone="warn"
                        value={valor(k.valorRemanescente, fmt.brl)}
                        hint="Quanto falta dos processos da Condenação que já tiveram o incontroverso pago; situação de hoje, sem período."
                    />
                    <HeroStat
                        label="Quantidade de saída da execução"
                        icon="check-circle"
                        tone="ok"
                        value={valor(k.saidas, fmt.int)}
                        below={
                            <span className="ex-below">
                                <DeltaPill value={k.compSaidas} suffix={VS} plain />
                                <span className="muted small">
                                    Qtd. incontroverso:{' '}
                                    <strong className="num">{fmt.int(k.saidasIncontroverso)}</strong>
                                </span>
                            </span>
                        }
                        hint="Condenação = alvará compensado; Acordos = acordo pago. Qtd. incontroverso = receberam só parte no período e aguardam o restante."
                    />
                    <HeroStat
                        label="Média de tempo"
                        icon="clock"
                        tone="info"
                        value={k.mediaTempo ? fmt.duracao(k.mediaTempo) : '0h'}
                        below={<DeltaPill value={k.compMediaTempo} betterWhenDown suffix={VS} plain />}
                        hint="Tempo médio da entrada à saída dos processos que saíram no período, juntando as durações da Condenação e dos Acordos."
                    />
                    <HeroStat
                        className="ex-ind-alto"
                        label="Estoque inicial do período anterior"
                        icon="scale"
                        tone="neutral"
                        value={valor(k.estoqueInicial, fmt.int)}
                        hint="Quantos estavam na Execução no início do período: o ponto de partida para entradas e saídas."
                    />
                    <HeroStat
                        label="Valor entrada na execução"
                        icon="dollar"
                        tone="info"
                        value={valor(k.valorEntrada, fmt.brl)}
                        below={
                            <span className="ex-below">
                                <DeltaPill value={k.compValorEntrada} suffix={VS} plain />
                                <span className="muted small">
                                    Ticket médio: <strong className="num">{fmt.brl(k.ticketEntrada)}</strong>
                                </span>
                            </span>
                        }
                        hint="Valor dos processos que entraram no período; ticket = valor ÷ quantidade de entradas."
                    />
                    <HeroStat
                        label="Valor incontroverso"
                        icon="dollar"
                        tone="accent"
                        value={valor(k.valorIncontroverso, fmt.brl)}
                        hint="Parte paga no período em processos da Condenação que aguardam o restante."
                    />
                    <HeroStat
                        label="Valor saída execução"
                        icon="dollar"
                        tone="ok"
                        value={valor(k.valorSaida, fmt.brl)}
                        below={
                            <span className="ex-below">
                                <DeltaPill value={k.compValorSaida} suffix={VS} plain />
                                <span className="muted small">
                                    Valor TED: <strong className="num">{fmt.brl(k.valorTed)}</strong>
                                </span>
                            </span>
                        }
                        hint="Alvarás compensados + acordos pagos no período (se parte já tinha sido paga, só o restante). Valor TED = o que de fato caiu na conta."
                    />
                    <HeroStat
                        label="Mediana de tempo"
                        icon="clock"
                        tone="info"
                        value={k.medianaTempo ? fmt.duracao(k.medianaTempo) : '0h'}
                        below={<DeltaPill value={k.compMedianaTempo} betterWhenDown suffix={VS} plain />}
                        hint="O tempo do processo do meio (entrada até saída) entre os que saíram no período; não é distorcida pelos extremos."
                    />
                </div>
                <div className="grid grid-stat-3 ex-mt">
                    {[
                        {
                            rotulo: 'Taxa de atualização de valores',
                            taxa: k.taxa?.total ?? null,
                            sub: '1G + 2G · só Execução Condenação',
                            delta: true,
                        },
                        ...['1G', '2G'].map((f) => {
                            const linha = k.taxa?.linhas.find((x) => x.fluxo === f)
                            return {
                                rotulo: f === '1G' ? 'Taxa 1G — sentença' : 'Taxa 2G — acórdão',
                                taxa: linha?.taxa ?? null,
                                sub: linha
                                    ? `${fmt.int(linha.quantidade)} processo(s) · aumento de ${fmt.brlShort(linha.aumento)}`
                                    : 'sem entradas no período',
                                delta: false,
                            }
                        }),
                    ].map((t) => (
                        <CardFiltro
                            key={t.rotulo}
                            onClick={() => setTaxaAberta(true)}
                            rotuloAcao={`Ver os detalhes: ${t.rotulo}`}
                        >
                            <MiniStat
                                label={t.rotulo}
                                icon="percent"
                                tone="info"
                                value={taxaTexto(t.taxa)}
                                below={
                                    <span className="ex-below">
                                        {t.delta && <DeltaPill value={k.compTaxa} suffix={VS} plain />}
                                        <span className="muted small">{t.sub} · ver detalhes</span>
                                    </span>
                                }
                                hint={
                                    t.delta
                                        ? 'Quanto o valor cresceu da decisão (sentença/acórdão) até a Execução, nas entradas da Condenação no período (1G vs sentença, 2G vs acórdão). Clique para ver os detalhes.'
                                        : undefined
                                }
                            />
                        </CardFiltro>
                    ))}
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Tendência"
                title="Entradas e saídas na execução por mês"
                subtitle={`Quantidade e valor mês a mês (todo o histórico, sem o período do calendário) e as distribuições — ${sufixo}.`}
            >
                <div className="grid dist-grid">
                    <ChartCard
                        title={`Entradas e saídas por mês${anoAtivo ? ` · ${anoAtivo}` : ''}`}
                        subtitle="Processos que entraram e saíram da Execução"
                        action={seletorAno}
                    >
                        <LineChart
                            height={300}
                            legend
                            labels={MESES}
                            tooltip={{ heading: 'Mês', title: mesNome }}
                            series={[
                                {
                                    label: 'Quantidade entrada',
                                    color: 'var(--chart-3)',
                                    values: doAno(s.qtdEntradaAno),
                                },
                                { label: 'Quantidade saída', color: 'var(--chart-1)', values: doAno(s.qtdSaidaAno) },
                            ]}
                        />
                    </ChartCard>
                    <ChartCard
                        title="Demonstrativo de matérias"
                        subtitle="Clique numa matéria para filtrar a página"
                        action={
                            <Segmented
                                label="Matérias"
                                options={[
                                    { value: 'total', label: 'Total' },
                                    { value: 'qtd_entrada', label: 'Qtd entrada' },
                                    { value: 'valor_entrada', label: 'Valor entrada' },
                                ]}
                                value={modoMateria}
                                onChange={setModoMateria}
                            />
                        }
                    >
                        <PieChart
                            items={materias}
                            size={240}
                            max={8}
                            labels
                            labelsTwoLines
                            format={modoMateria === 'valor_entrada' ? fmt.brlShort : fmt.int}
                            centerFormat={modoMateria === 'valor_entrada' ? fmt.eixo : undefined}
                            centerLabel={modoMateria === 'valor_entrada' ? 'valor de entrada' : 'processos'}
                            selected={filters.materia}
                            onSelect={alternar && ((v) => v !== 'Outras' && alternar('materia', v))}
                            selectLabel="Filtrar pela matéria"
                        />
                    </ChartCard>
                </div>
                <ChartCard
                    className="ex-mt"
                    title={`Entradas por fluxo${anoAtivo ? ` · ${anoAtivo}` : ''}`}
                    subtitle="1G e 2G vindas da Confecção CS (Elaborar CS ou Manifestação Cálculo), Outros por outro caminho, e Acordos fechados no mês"
                >
                    <LineChart
                        height={300}
                        legend
                        labels={MESES}
                        tooltip={{ heading: 'Mês', title: mesNome }}
                        series={[
                            ...(l.incluirCondenacao
                                ? [
                                      { label: '1G', color: 'var(--chart-3)', values: fluxoDoAno('1G') },
                                      { label: '2G', color: 'var(--chart-1)', values: fluxoDoAno('2G') },
                                      ...(s.temSemGrau
                                          ? [
                                                {
                                                    label: 'CS (sem grau)',
                                                    color: 'var(--chart-5)',
                                                    values: fluxoDoAno('CS (sem grau)'),
                                                },
                                            ]
                                          : []),
                                      { label: 'Outros', color: 'var(--text-muted)', values: fluxoDoAno('Outros') },
                                  ]
                                : []),
                            ...(l.incluirAcordos
                                ? [{ label: 'Acordos', color: 'var(--ok-dot)', values: doAno(s.acordosEntradaAno) }]
                                : []),
                        ]}
                    />
                </ChartCard>
                <div className="grid dist-grid ex-mt">
                    <ChartCard
                        title="Valor de entrada na execução por mês"
                        subtitle="Comparado por ano; não depende do período"
                        tag={<Pill>Por ano</Pill>}
                    >
                        <PorAno mapa={s.valorEntradaAno} format={fmt.brlShort} />
                    </ChartCard>
                    <ChartCard
                        className="ex-rolagem"
                        title="Valor por subfase"
                        subtitle="Condenação: valor da execução; Acordos: alçada final · clique para filtrar"
                        action={
                            <Segmented
                                label="Subfases"
                                options={[
                                    { value: 'total', label: 'Total' },
                                    { value: 'entrada', label: 'Entrada' },
                                ]}
                                value={modoSubfase}
                                onChange={setModoSubfase}
                            />
                        }
                    >
                        <BarList
                            items={dist.subfase[modoSubfase]}
                            format={fmt.brlShort}
                            valueOutside
                            wrapNames
                            selected={filters.subfase}
                            onSelect={alternar && ((v) => alternar('subfase', v))}
                            selectLabel="Filtrar pela subfase"
                        />
                    </ChartCard>
                </div>
                <div className="grid ex-duo ex-pizzas ex-mt">
                    {[
                        {
                            titulo: 'Ano de ajuizamento das entradas',
                            sub: 'Processos que entraram no período',
                            itens: dist.anoEntradas,
                        },
                        {
                            titulo: 'Ano de ajuizamento — total em execução',
                            sub: 'Todos os processos em Execução agora',
                            itens: dist.anoTotal,
                        },
                    ].map((p) => (
                        <ChartCard
                            key={p.titulo}
                            title={p.titulo}
                            subtitle={`${p.sub} · valor de causa ${fmt.brlShort(p.itens.reduce((t, x) => t + x.valorCausa, 0))} · clique num ano para filtrar`}
                        >
                            <PieChart
                                items={p.itens.map((x) => ({ name: x.name, value: x.value }))}
                                sort={false}
                                size={240}
                                labels
                                labelsTwoLines
                                centerLabel="processos"
                                selected={filters.ano_ajuizamento}
                                onSelect={escolher && ((v) => escolher('ano_ajuizamento', v))}
                                selectLabel="Filtrar pelo ano"
                            />
                        </ChartCard>
                    ))}
                </div>
                <ChartCard
                    className="ex-mt"
                    title={`Valor de entrada e saída por mês${anoAtivo ? ` · ${anoAtivo}` : ''}`}
                    subtitle="Mesmo ano do seletor da seção"
                >
                    <LineChart
                        height={300}
                        legend
                        format={fmt.brlShort}
                        labels={MESES}
                        tooltip={{ heading: 'Mês', title: mesNome }}
                        series={[
                            { label: 'Valor de entrada', color: 'var(--chart-3)', values: doAno(s.valorEntradaAno) },
                            { label: 'Valor de saída', color: 'var(--chart-1)', values: doAno(s.valorSaidaAno) },
                        ]}
                    />
                </ChartCard>
                <div className="grid ex-duo ex-mt">
                    <ChartCard
                        title="Tempo médio em dias — execução por mês"
                        subtitle="Comparado por ano. Com Condenação e Acordos juntos, soma o tempo médio dos dois lados (como a v1)"
                        tag={<Pill>Por ano</Pill>}
                    >
                        <PorAno mapa={s.tempoMedioAno} format={(v) => fmt.dec1(v)} />
                    </ChartCard>
                    <ChartCard
                        title="Ticket médio entrada — execução por mês"
                        subtitle="Valor de entrada ÷ quantidade, comparado por ano"
                        tag={<Pill>Por ano</Pill>}
                    >
                        <PorAno mapa={s.ticketAno} format={fmt.brlShort} />
                    </ChartCard>
                </div>
                <div className="grid dist-grid ex-mt">
                    <ComarcasCard
                        comarcas={comarcas}
                        modo={modoComarca}
                        setModo={setModoComarca}
                        selecionadas={filters.comarca ?? []}
                        onSelect={alternar && ((v) => alternar('comarca', v))}
                    />
                    <ChartCard
                        title="Condenação x Acordos"
                        subtitle="Clique numa fatia para ver só aquele lado"
                        action={
                            <Segmented
                                label="Condenação x Acordos"
                                options={[
                                    { value: 'total', label: 'Total' },
                                    { value: 'entrada', label: 'Entradas' },
                                    { value: 'saida', label: 'Saídas' },
                                ]}
                                value={modoCxA}
                                onChange={setModoCxA}
                            />
                        }
                    >
                        <PieChart
                            items={dist.condenacaoAcordos[modoCxA]}
                            sort={false}
                            size={240}
                            labels
                            labelsTwoLines
                            centerLabel="processos"
                            selected={
                                escopo === 'condenacao' ? ['Condenação'] : escopo === 'acordos' ? ['Acordos'] : []
                            }
                            onSelect={
                                escolher && ((v) => escolher('escopo', v === 'Condenação' ? 'condenacao' : 'acordos'))
                            }
                            selectLabel="Ver só"
                        />
                    </ChartCard>
                </div>
            </DashSection>

            {l.incluirCondenacao && (
                <DashSection
                    index={3}
                    eyebrow="Gargalos"
                    title="Confecção CS"
                    subtitle="Elaborar Cumprimento de Sentença e Manifestação Cálculo 1 e 2: onde as atividades travam o crescimento."
                >
                    <div className="grid grid-stat-3">
                        <MiniStat
                            label="Total de atividades"
                            icon="list"
                            tone="neutral"
                            value={cs.total === null ? '—' : fmt.int(cs.total)}
                            below={<span className="muted small">criadas no período</span>}
                            hint="Tarefas que chegaram na Confecção CS no período, mesmo as já concluídas; canceladas não entram."
                        />
                        <CardFiltro onClick={() => setListaCS('abertas')} rotuloAcao="Ver as atividades em andamento">
                            <MiniStat
                                label="Em andamento"
                                icon="flow"
                                tone="warn"
                                value={cs.abertas === null ? '—' : fmt.int(cs.abertas)}
                                below={
                                    <span className="muted small">em aberto, acumulado sem período · ver lista</span>
                                }
                            />
                        </CardFiltro>
                        <CardFiltro onClick={() => setListaCS('concluidas')} rotuloAcao="Ver as atividades concluídas">
                            <MiniStat
                                label="Concluídas"
                                icon="check-circle"
                                tone="ok"
                                value={cs.concluidas === null ? '—' : fmt.int(cs.concluidas)}
                                below={<span className="muted small">encerradas no período · ver lista</span>}
                            />
                        </CardFiltro>
                    </div>
                    {filters.funcionario_execucao?.length ||
                    filters.situacao_execucao?.length ||
                    selAtividade.length ? (
                        <div className="ex-toolbar ex-mt">
                            <div className="ex-chips">
                                {[
                                    ...selAtividade.map((v) => ['atividade_execucao', 'Atividade', v] as const),
                                    ...(filters.funcionario_execucao ?? []).map(
                                        (v) => ['funcionario_execucao', 'Funcionário', v] as const,
                                    ),
                                ].map(([key, rot, v]) => (
                                    <span key={`${key}:${v}`} className="chip">
                                        {rot}: {v}
                                        <button
                                            type="button"
                                            aria-label={`Tirar o filtro ${rot}: ${v}`}
                                            onClick={() => alternar?.(key, v)}
                                        >
                                            <Icon name="close" size={12} />
                                        </button>
                                    </span>
                                ))}
                                <button
                                    type="button"
                                    className="linkbtn muted"
                                    onClick={() =>
                                        set?.(
                                            clearFilter(
                                                clearFilter(
                                                    clearFilter(filters, 'atividade_execucao'),
                                                    'funcionario_execucao',
                                                ),
                                                'situacao_execucao',
                                            ),
                                        )
                                    }
                                >
                                    Limpar filtros
                                </button>
                            </div>
                        </div>
                    ) : null}
                    <div className="grid dist-grid ex-mt">
                        <ChartCard
                            className="ex-rolagem"
                            title="Por atividade"
                            subtitle="Concluídas e em aberto · clique numa atividade para ver só ela"
                        >
                            <StackedBars
                                rows={cs.porAtividade.map((a) => ({ name: a.name, values: [a.concluidos, a.abertas] }))}
                                parts={[
                                    { label: 'Concluídos', color: 'var(--chart-1)' },
                                    { label: 'Em aberto', color: 'var(--text-muted)' },
                                ]}
                                selected={selAtividade}
                                onSelect={escolher && ((v) => escolher('atividade_execucao', v))}
                                selectLabel="Ver só a atividade"
                            />
                        </ChartCard>
                        <ChartCard
                            className="ex-rolagem"
                            title="Demandas por funcionário (cumpridas)"
                            subtitle={
                                cs.concluidas !== null && cs.abertas !== null && cs.concluidas + cs.abertas > 0
                                    ? `${fmt.int(cs.concluidas)} concluídas de ${fmt.int(cs.concluidas + cs.abertas)} (${fmt.int(cs.abertas)} em aberto) · % = taxa de conclusão de cada um`
                                    : 'Clique num funcionário para filtrar a seção'
                            }
                        >
                            <BarList
                                items={cs.porFuncionario.map((f) => ({
                                    name: f.percent === null ? f.name : `${f.name} · ${fmt.dec1(f.percent)}%`,
                                    value: f.cumpridas,
                                }))}
                                wrapNames
                                valueOutside
                                selected={(filters.funcionario_execucao ?? []).flatMap((n) =>
                                    cs.porFuncionario
                                        .filter((f) => f.name === n)
                                        .map((f) =>
                                            f.percent === null ? f.name : `${f.name} · ${fmt.dec1(f.percent)}%`,
                                        ),
                                )}
                                onSelect={
                                    alternar &&
                                    ((rotulo) => {
                                        const nome = rotulo.replace(/ · [\d.,]+%$/, '')
                                        if (nome && nome !== 'Sem funcionário identificado')
                                            alternar('funcionario_execucao', nome)
                                    })
                                }
                                selectLabel="Filtrar pelo funcionário"
                            />
                        </ChartCard>
                    </div>
                    {cs.motivos.length > 0 && (
                        <ChartCard
                            className="ex-mt"
                            title="Motivo do não cumprimento"
                            subtitle="Registrados ao encerrar como 'Encerrado Não Cumprido' (todo o histórico)"
                        >
                            <BarList items={cs.motivos} wrapNames />
                        </ChartCard>
                    )}
                </DashSection>
            )}

            <DashSection
                index={l.incluirCondenacao ? 4 : 3}
                eyebrow="Compensação"
                title="Alvarás expedidos"
                subtitle="Processos com alvará já expedido aguardando compensação em conta, conforme o escopo selecionado."
            >
                <AlvarasGrafico
                    condenacao={l.incluirCondenacao ? alv.condenacao : null}
                    acordos={l.incluirAcordos ? alv.acordos : null}
                />
                <div className="ex-mt">
                    <AlvarasLista linhas={alv.lista} />
                </div>
            </DashSection>

            {taxaAberta && <TaxaModal taxa={k.taxa} onClose={() => setTaxaAberta(false)} />}
            {listaCS && (
                <AtividadesCSModal
                    tipo={listaCS}
                    tarefas={listaCS === 'abertas' ? cs.abertasLista : cs.concluidasLista}
                    onClose={() => setListaCS(null)}
                />
            )}
        </div>
    )
}

// "Processos por comarca" da v1: quantidade, valor e tempo médio, com Total / Entradas / Saídas.
function ComarcasCard({
    comarcas,
    modo,
    setModo,
    selecionadas,
    onSelect,
}: {
    comarcas: Comarca[]
    modo: 'total' | 'entrada' | 'saida'
    setModo: (m: 'total' | 'entrada' | 'saida') => void
    selecionadas: string[]
    onSelect?: (c: string) => void
}) {
    const p = usePagina(comarcas, 8)
    return (
        <ChartCard
            title="Processos por comarca"
            subtitle={`${fmt.int(comarcas.length)} comarca(s) · ${fmt.int(comarcas.reduce((t, c) => t + c.value, 0))} processos · clique para filtrar`}
            action={
                <Segmented
                    label="Comarcas"
                    options={[
                        { value: 'total', label: 'Total' },
                        { value: 'entrada', label: 'Entradas' },
                        { value: 'saida', label: 'Saídas' },
                    ]}
                    value={modo}
                    onChange={setModo}
                />
            }
        >
            <DataTable
                rows={p.itens}
                rowKey={(c) => c.name}
                empty="Nenhuma comarca nesse recorte."
                rowClassName={(c) => (selecionadas.length > 0 && !selecionadas.includes(c.name) ? 'ex-dim' : undefined)}
                columns={[
                    {
                        header: 'Comarca',
                        render: (c) =>
                            onSelect ? (
                                <button
                                    type="button"
                                    className="linkbtn"
                                    aria-pressed={selecionadas.includes(c.name)}
                                    onClick={() => onSelect(c.name)}
                                >
                                    {c.name || '—'}
                                </button>
                            ) : (
                                c.name
                            ),
                    },
                    { header: 'Processos', align: 'right', render: (c) => fmt.int(c.value) },
                    { header: 'Valor', align: 'right', render: (c) => fmt.brl(c.valor) },
                    {
                        header: 'Tempo médio',
                        align: 'right',
                        render: (c) => (c.tempoMedio === null ? '—' : dias(c.tempoMedio)),
                    },
                ]}
            />
            <Paginador pagina={p.pagina} total={p.total} onChange={p.setPagina} />
        </ChartCard>
    )
}

// O gráfico de alvarás da v1: por mês (quantidade e valor) de um ano; clicar num mês mostra os dias.
function AlvarasGrafico({ condenacao, acordos }: { condenacao: AlvaraDia[] | null; acordos: AlvaraDia[] | null }) {
    const origens = [
        ...(condenacao && acordos ? [{ value: 'todos', label: 'Todos' }] : []),
        ...(condenacao ? [{ value: 'condenacao', label: 'Condenação' }] : []),
        ...(acordos ? [{ value: 'acordos', label: 'Acordos' }] : []),
    ]
    const [origem, setOrigem] = useState('todos')
    const ativa = origens.some((o) => o.value === origem) ? origem : (origens[0]?.value ?? 'todos')
    const linhas =
        ativa === 'condenacao'
            ? (condenacao ?? [])
            : ativa === 'acordos'
              ? (acordos ?? [])
              : [...(condenacao ?? []), ...(acordos ?? [])]
    const anos = [...new Set(linhas.map((d) => d.data.slice(0, 4)).filter(Boolean))].sort()
    const [ano, setAno] = useState<string | null>(null)
    const anoAtivo = ano && anos.includes(ano) ? ano : (anos.at(-1) ?? null)
    const [mes, setMes] = useState<number | null>(null)
    const [metrica, setMetrica] = useState<'quantidade' | 'valor'>('quantidade')
    if (!anoAtivo) return <ChartEmpty>Não há dados de alvarás expedidos.</ChartEmpty>
    const porMes = alvarasPorMes(linhas, anoAtivo)
    const porDia = mes !== null ? alvarasPorDia(linhas, anoAtivo, mes) : null
    const categorias = porDia
        ? Array.from(
              { length: porDia.dias },
              (_, i) => `${String(i + 1).padStart(2, '0')}/${String((mes ?? 0) + 1).padStart(2, '0')}`,
          )
        : MES_CURTO
    const qtd = porDia ? porDia.qtd : porMes.qtd
    const val = porDia ? porDia.valor : porMes.valor
    const acoes = (
        <div className="ex-acoes">
            {origens.length > 1 && <Segmented label="Origem" options={origens} value={ativa} onChange={setOrigem} />}
            <Segmented
                label="Métrica"
                options={[
                    { value: 'quantidade', label: 'Quantidade' },
                    { value: 'valor', label: 'Valor' },
                ]}
                value={metrica}
                onChange={setMetrica}
            />
            {porDia ? (
                <button type="button" className="btn" onClick={() => setMes(null)}>
                    <Icon name="undo" size={15} /> Meses
                </button>
            ) : (
                <label className="field-select">
                    <span className="sr-only">Ano</span>
                    <select value={anoAtivo} onChange={(e) => setAno(e.target.value)}>
                        {anos.map((a) => (
                            <option key={a} value={a}>
                                {a}
                            </option>
                        ))}
                    </select>
                </label>
            )}
        </div>
    )
    const titulo = porDia ? ` por dia — ${mesNome(mes ?? 0)} ${anoAtivo}` : ` por mês — ${anoAtivo}`
    const comValor = metrica === 'valor'
    return (
        <ChartCard
            title={`Alvarás expedidos${titulo}`}
            subtitle={`${fmt.int(qtd.reduce((t, v) => t + v, 0))} alvará(s) · ${fmt.brl(val.reduce((t, v) => t + v, 0))}${porDia ? '' : ' · clique num mês para ver os dias'}`}
            action={acoes}
        >
            <div key={`${anoAtivo}-${mes}-${metrica}`} className="ex-drill">
                <ColumnChart
                    height={280}
                    tooltip
                    format={comValor ? fmt.brlShort : undefined}
                    categories={categorias}
                    series={[
                        comValor
                            ? { label: 'Valor', color: 'var(--chart-1)', values: val }
                            : { label: 'Quantidade', color: 'var(--chart-3)', values: qtd },
                    ]}
                    onSelect={porDia ? undefined : (c) => setMes(MES_CURTO.indexOf(c))}
                    selectLabel="Ver os dias de"
                />
            </div>
        </ChartCard>
    )
}

type Ordem = 'expedicao' | 'previsao' | 'prazo' | 'valor'

// A lista de alvarás expedidos da v1: previsão de compensação (expedição + 5 dias úteis) e o prazo até ela.
function AlvarasLista({ linhas }: { linhas: Alvara[] }) {
    const [ordem, setOrdem] = useState<{ chave: Ordem; asc: boolean } | null>(null)
    const hoje = hojeIso()
    const comPrazo = linhas.map((a) => {
        const previsao = a.expedicao ? previsaoCompensacao(a.expedicao) : null
        return { ...a, previsao, faltam: previsao ? diasUteisAte(previsao, hoje) : null }
    })
    const chave = (a: (typeof comPrazo)[number]): string | number | null =>
        ordem?.chave === 'valor'
            ? a.valor
            : ordem?.chave === 'prazo'
              ? a.faltam
              : ordem?.chave === 'previsao'
                ? a.previsao
                : a.expedicao
    const ordenadas = ordem
        ? [...comPrazo].sort((x, y) => {
              const a = chave(x)
              const b = chave(y)
              if (a === null) return 1
              if (b === null) return -1
              const c = a < b ? -1 : a > b ? 1 : 0
              return ordem.asc ? c : -c
          })
        : comPrazo
    const p = usePagina(ordenadas, 20)
    const total = linhas.reduce((t, a) => t + (a.valor ?? 0), 0)
    const cab = (rotulo: string, c: Ordem) => (
        <button
            type="button"
            className="linkbtn"
            onClick={() => setOrdem((o) => (o?.chave === c ? { chave: c, asc: !o.asc } : { chave: c, asc: true }))}
        >
            {rotulo}
            {ordem?.chave === c ? (ordem.asc ? ' ↑' : ' ↓') : ''}
        </button>
    )
    const prazo = (f: number | null) =>
        f === null
            ? '—'
            : f > 0
              ? f > 1
                  ? `Faltam ${f} dias úteis`
                  : 'Falta 1 dia útil'
              : f === 0
                ? 'Previsto para hoje'
                : `${-f} dia${f < -1 ? 's úteis' : ' útil'} de atraso`
    return (
        <ChartCard
            title="Alvarás expedidos"
            subtitle="Aguardando compensação: Condenação (Alvará Expedido e Alvará do Incontroverso Expedido) e Acordos (Alvará Expedido Acordo). A compensação é prevista para 5 dias úteis após a expedição."
            action={
                <span className="muted small num">
                    {fmt.int(linhas.length)} processo(s) · {fmt.brl(total)}
                </span>
            }
        >
            <div className="ex-lista compacta">
                <DataTable
                    rows={p.itens}
                    rowKey={(a) => `${a.processo}-${a.expedicao}-${a.tipo}`}
                    empty="Nenhum processo com alvará expedido no momento."
                    columns={[
                        {
                            header: 'Nº do processo',
                            render: (a) => <span className="num">{numeroCnj(a.processo)}</span>,
                        },
                        {
                            header: 'Origem',
                            render: (a) => (
                                <span className="ex-tarefa">
                                    <Pill tone={a.origem === 'Acordo' ? 'ok' : 'info'}>{a.origem}</Pill>
                                    {a.tipo && a.tipo !== 'Acordo' && <span className="muted small">{a.tipo}</span>}
                                </span>
                            ),
                        },
                        {
                            header: 'Subfase',
                            render: (a) => (
                                <span
                                    className="ex-corta ex-corta-curta"
                                    title={a.materia ? `${a.subfase} · ${a.materia}` : a.subfase}
                                >
                                    {a.subfase || '—'}
                                </span>
                            ),
                        },
                        {
                            header: cab('Expedição', 'expedicao'),
                            render: (a) => (
                                <span className="ex-tarefa num">
                                    {a.expedicao ? diaLongo(a.expedicao.slice(0, 10)) : '—'}
                                    {a.tipo === 'Remanescente' && a.expedicaoIncontroverso && (
                                        <span className="muted small">
                                            Incontr. {diaLongo(a.expedicaoIncontroverso.slice(0, 10))}
                                        </span>
                                    )}
                                </span>
                            ),
                        },
                        {
                            header: cab('Previsão', 'previsao'),
                            render: (a) => <span className="num">{a.previsao ? diaLongo(a.previsao) : '—'}</span>,
                        },
                        {
                            header: cab('Prazo', 'prazo'),
                            render: (a) => (
                                <span
                                    className={
                                        a.faltam === null
                                            ? 'muted'
                                            : a.faltam < 0
                                              ? 'tone-text-danger'
                                              : a.faltam === 0
                                                ? 'tone-text-warn'
                                                : 'tone-text-info'
                                    }
                                >
                                    {prazo(a.faltam)}
                                </span>
                            ),
                        },
                        {
                            header: cab('Valor do alvará', 'valor'),
                            align: 'right',
                            render: (a) => (
                                <span className="ex-tarefa num">
                                    {a.valor === null ? '—' : fmt.brl(a.valor)}
                                    {a.tipo === 'Remanescente' && a.valorIncontroverso !== null && (
                                        <span className="muted small">Incontr. {fmt.brl(a.valorIncontroverso)}</span>
                                    )}
                                </span>
                            ),
                        },
                    ]}
                />
            </div>
            <Paginador pagina={p.pagina} total={p.total} onChange={p.setPagina} />
        </ChartCard>
    )
}

// O modal da Taxa de Atualização (v1: ExecucaoTaxaAtualizacaoModal).
function TaxaModal({ taxa, onClose }: { taxa: TaxaAtualizacao | null; onClose: () => void }) {
    const [agora] = useState(() => new Date())
    const ano = taxa?.ano ?? agora.getFullYear()
    const ultimoMes = ano === agora.getFullYear() ? agora.getMonth() + 1 : 12
    const meses = Array.from({ length: ultimoMes }, (_, i) => taxa?.porMes.find((m) => m.mes === i + 1) ?? null)
    const temMes = meses.some((m) => m?.taxa != null)
    const fluxo = (f: string) => (f === '1G' ? '1G — Sentença' : f === '2G' ? '2G — Acórdão' : f)
    return (
        <Modal
            title="Taxa de atualização de valores"
            description="Quanto o valor cresceu da decisão até a Execução, nas entradas da Execução Condenação no período que vieram da Confecção CS: 1G compara o valor da sentença e 2G o valor do acórdão com o valor da execução."
            className="ex-modal"
            onClose={onClose}
        >
            {!taxa ? (
                <ChartEmpty>Sem dados de taxa de atualização no período.</ChartEmpty>
            ) : (
                <div className="ex-modal-corpo">
                    <DataTable
                        rows={taxa.linhas}
                        rowKey={(r) => r.fluxo}
                        empty="Sem entradas no período."
                        columns={[
                            {
                                header: 'Fluxo',
                                render: (r) => (
                                    <span className="ex-tarefa">
                                        <strong>{fluxo(r.fluxo)}</strong>
                                        <span className="muted small">{fmt.int(r.quantidade)} processo(s)</span>
                                    </span>
                                ),
                            },
                            { header: 'Valor da decisão', align: 'right', render: (r) => fmt.brl(r.valorDecisao) },
                            { header: 'Valor da execução', align: 'right', render: (r) => fmt.brl(r.valorExecucao) },
                            { header: 'Aumento', align: 'right', render: (r) => fmt.brl(r.aumento) },
                            {
                                header: 'Taxa de atualização',
                                align: 'right',
                                render: (r) => <strong>{taxaTexto(r.taxa)}</strong>,
                            },
                        ]}
                    />
                    <p className="small">
                        Taxa total (1G + 2G): <strong>{taxaTexto(taxa.total)}</strong> — taxa = (valor da execução −
                        valor da decisão) ÷ valor da decisão, somando os processos de cada fluxo.
                    </p>
                    <ChartCard
                        title={`Mês a mês — ${ano}`}
                        subtitle="Pelo mês da entrada na Execução, independente do período selecionado"
                    >
                        {temMes ? (
                            <div className="grid ex-duo">
                                <LineChart
                                    height={240}
                                    legend
                                    format={fmt.brlShort}
                                    labels={MESES.slice(0, ultimoMes)}
                                    tooltip={{ heading: 'Mês', title: mesNome }}
                                    series={[
                                        {
                                            label: 'Valor da sentença',
                                            color: 'var(--chart-3)',
                                            values: meses.map((m) => (m ? m.valorSentenca : null)),
                                        },
                                        {
                                            label: 'Valor do acórdão',
                                            color: 'var(--chart-1)',
                                            values: meses.map((m) => (m ? m.valorAcordao : null)),
                                        },
                                    ]}
                                />
                                <LineChart
                                    height={240}
                                    legend
                                    format={(v) => `${fmt.dec1(v)}%`}
                                    labels={MESES.slice(0, ultimoMes)}
                                    tooltip={{ heading: 'Mês', title: mesNome }}
                                    series={[
                                        {
                                            label: 'Taxa de atualização',
                                            color: 'var(--ok-dot)',
                                            values: meses.map((m) => m?.taxa ?? null),
                                            dashed: true,
                                        },
                                    ]}
                                />
                            </div>
                        ) : (
                            <ChartEmpty>Sem entradas com valores neste ano.</ChartEmpty>
                        )}
                    </ChartCard>
                    <ChartCard
                        title={`Processos sem valor preenchido (${fmt.int(taxa.semValor.length)})`}
                        subtitle="Entradas do período que ficaram fora da taxa por falta do valor da decisão e/ou da execução"
                    >
                        <DataTable
                            rows={taxa.semValor}
                            rowKey={(r) => `${r.processo}-${r.fluxo}`}
                            empty="Todas as entradas do período têm os valores preenchidos."
                            columns={[
                                {
                                    header: 'Nº do processo',
                                    render: (r) => <span className="num">{numeroCnj(r.processo)}</span>,
                                },
                                { header: 'Fluxo', render: (r) => r.fluxo },
                                {
                                    header: 'Entrada na Execução',
                                    render: (r) => (r.dataEntrada ? diaLongo(r.dataEntrada.slice(0, 10)) : '—'),
                                },
                                { header: 'Valor faltando', render: (r) => r.faltando.join(' e ') },
                            ]}
                        />
                    </ChartCard>
                </div>
            )}
        </Modal>
    )
}

// O modal das atividades da Confecção CS (v1: ExecucaoAtividadesListaModal): em andamento (com o atraso) ou
// concluídas (com a situação do prazo), 5 por página.
function AtividadesCSModal({
    tipo,
    tarefas,
    onClose,
}: {
    tipo: 'abertas' | 'concluidas'
    tarefas: TarefaCS[]
    onClose: () => void
}) {
    const p = usePagina(tarefas, 5)
    const [hoje] = useState(() => {
        const d = new Date()
        return Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())
    })
    const diasEntre = (de: string, ate: number) =>
        Math.round((ate - Date.parse(`${de.slice(0, 10)}T00:00:00Z`)) / 86_400_000)
    const situacaoAberta = (t: TarefaCS) => {
        if (!t.prazo) return <span className="muted">—</span>
        const d = diasEntre(t.prazo, hoje)
        return d > 0 ? (
            <span className="tone-text-danger">{d} dia(s) em atraso</span>
        ) : d === 0 ? (
            <span className="tone-text-warn">Vence hoje</span>
        ) : (
            <span className="muted">Faltam {-d} dia(s)</span>
        )
    }
    const situacaoConcluida = (t: TarefaCS) => {
        if (!t.prazo || !t.concluidoEm) return <span className="muted">—</span>
        const d = diasEntre(t.prazo, Date.parse(`${t.concluidoEm.slice(0, 10)}T00:00:00Z`))
        return d > 0 ? (
            <span className="tone-text-danger">Cumprido com {d} dia(s) de atraso</span>
        ) : (
            <span className="tone-text-ok">Cumprido no prazo</span>
        )
    }
    const data = (iso: string | null) => (iso ? diaLongo(iso.slice(0, 10)) : '—')
    return (
        <Modal
            title={tipo === 'abertas' ? 'Em andamento — Confecção CS' : 'Concluídas — Confecção CS'}
            subtitle={`${fmt.int(tarefas.length)} atividade(s)`}
            description={
                tipo === 'abertas'
                    ? 'Todas as atividades ainda não concluídas, acumulado sem filtro de período — inclui as que já venceram o prazo.'
                    : 'Atividades encerradas (Cumprido ou Não Cumprido) no período selecionado.'
            }
            className="ex-modal"
            onClose={onClose}
        >
            <DataTable
                rows={p.itens}
                rowKey={(t) => t.id}
                empty="Nenhuma atividade encontrada."
                columns={[
                    { header: 'Nº do processo', render: (t) => <span className="num">{numeroCnj(t.processo)}</span> },
                    { header: 'Criação', render: (t) => <span className="num">{data(t.criadoEm)}</span> },
                    { header: 'Prazo', render: (t) => <span className="num">{data(t.prazo)}</span> },
                    ...(tipo === 'abertas'
                        ? [{ header: 'Situação do prazo', render: situacaoAberta }]
                        : [
                              {
                                  header: 'Conclusão',
                                  render: (t: TarefaCS) => <span className="num">{data(t.concluidoEm)}</span>,
                              },
                              { header: 'Situação', render: situacaoConcluida },
                          ]),
                    {
                        header: 'Valor da sentença',
                        align: 'right' as const,
                        render: (t: TarefaCS) => (t.valorSentenca === null ? '—' : fmt.brl(t.valorSentenca)),
                    },
                    {
                        header: 'Valor do acórdão',
                        align: 'right' as const,
                        render: (t: TarefaCS) => (t.valorAcordao === null ? '—' : fmt.brl(t.valorAcordao)),
                    },
                ]}
            />
            <Paginador pagina={p.pagina} total={p.total} onChange={p.setPagina} />
        </Modal>
    )
}
