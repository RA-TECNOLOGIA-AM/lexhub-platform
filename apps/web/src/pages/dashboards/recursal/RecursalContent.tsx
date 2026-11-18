import { useState } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { GaugeChart } from '../../../components/charts/GaugeChart.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { StackedBars } from '../../../components/charts/StackedBars.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { FootRow, HeroStat, MiniStat, Pill } from '../../../components/dashboard/StatCard.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { Modal } from '../../../components/ui/Modal.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { toggleFilter } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import type { ContentProps } from '../types.ts'
import { ListaTarefas, ProducaoDiaria } from '../execucao/AtividadesSection.tsx'
import { CardFiltro } from '../execucao/partes.tsx'
import {
    DECISOES,
    MATRIZ,
    MATRIZ_1G,
    MATRIZ_2G,
    celulaMarcada,
    clicarCelula,
    filtroDecisao,
    lerRecursal,
    producaoDias,
    tomTaxa,
    type Linha,
    type Magistrado,
    type RecursalResponse,
    type VisaoRecursal,
} from './recursal.ts'

type Base = 'estoque' | 'entrada'
const BASES: { value: Base; label: string }[] = [
    { value: 'estoque', label: 'Total (estoque)' },
    { value: 'entrada', label: 'Entrada no período' },
]
const VISOES: { value: VisaoRecursal; label: string }[] = [
    { value: 'por_prazo', label: 'Por prazo' },
    { value: 'concluidas', label: 'Concluídas' },
]
const valor = (v: number | null, format: (n: number) => string) =>
    v === null ? '—' : <CountUp value={v} format={format} />
const pct = (v: number) => `${fmt.dec1(v)}%`

// O Recursal (NG, LA e RJ): as seções da página da v1 (NG/Recursal.tsx) no layout da V2. Clicar nos cards e
// gráficos filtra a página (como na v1, cada gráfico continua mostrando todas as fatias da própria dimensão).
export function RecursalContent({ data, filters = {}, onFiltersChange }: ContentProps<RecursalResponse>) {
    const r = lerRecursal(data)
    const [baseSubfase, setBaseSubfase] = useState<Base>('estoque')
    const [baseDist, setBaseDist] = useState<Base>('estoque')
    const [visao, setVisao] = useState<VisaoRecursal>('por_prazo')
    const [matrizAberta, setMatrizAberta] = useState(false)
    const set = onFiltersChange
    const alternar = set && ((key: keyof DashboardFilters, v: string) => set(toggleFilter(filters, key, v)))
    const marcados = (key: keyof DashboardFilters) => filters[key] ?? []
    const sub = r.distribuicao(baseSubfase)
    const dist = r.distribuicao(baseDist)
    const funcionarios = marcados('funcionario_recursos')
    const k = r.kpis[visao]
    const percentDo = (v: number | null) => (k.total && v !== null ? `${fmt.dec1((v / k.total) * 100)}% do total` : '')

    // Status 1G/2G: o gráfico mostra o rótulo; o filtro guarda o id.
    const statusSelecionados = (linhasStatus: Linha[], key: 'id_1g_recursal' | 'id_2g_recursal') =>
        linhasStatus.filter((l) => l.id !== null && marcados(key).includes(String(l.id))).map((l) => l.name)
    const clicarStatus = (linhasStatus: Linha[], key: 'id_1g_recursal' | 'id_2g_recursal') => (nome: string) => {
        const id = linhasStatus.find((l) => l.name === nome)?.id
        if (id !== null && id !== undefined) alternar?.(key, String(id))
    }

    // "Atribuição" da v1: com um funcionário só escolhido, as dele e quem encerrou.
    const um = funcionarios.length === 1 ? funcionarios[0] : null
    const atribuicao = um
        ? {
              atribuidas: r.lista.filter((t) => t.responsavel === um).length,
              porOutros: r.lista.filter((t) => t.encerradoPor !== null).length,
          }
        : null

    const cardsAtividade: { key: string; label: string; v: number | null; icon: IconName; tone: Tone; nota: string }[] =
        [
            {
                key: 'total',
                label: 'Total de atividades',
                v: k.total,
                icon: 'list',
                tone: 'neutral',
                nota: visao === 'por_prazo' ? 'com prazo no período' : 'criadas no período',
            },
            {
                key: 'em_andamento',
                label: 'Em andamento',
                v: k.emAndamento,
                icon: 'flow',
                tone: 'info',
                nota: 'abertas (Recebido / Visualizado)',
            },
            {
                key: 'vencidas',
                label: 'Vencidas',
                v: k.vencidas,
                icon: 'alert',
                tone: 'danger',
                nota: percentDo(k.vencidas) || 'prazo já passou',
            },
            {
                key: 'vencem_hoje',
                label: 'Vencem hoje',
                v: k.vencemHoje,
                icon: 'calendar',
                tone: 'warn',
                nota: 'prazo no dia atual',
            },
            {
                key: 'concluidas',
                label: 'Concluídas',
                v: k.concluidas,
                icon: 'check-circle',
                tone: 'ok',
                nota: 'encerradas no período',
            },
            ...(r.cancelados === null
                ? []
                : [
                      {
                          key: 'canceladas',
                          label: 'Cancelados',
                          v: r.cancelados,
                          icon: 'x-circle' as IconName,
                          tone: 'danger' as Tone,
                          nota: 'recurso cancelado no período',
                      },
                  ]),
        ]
    const situacoes = marcados('situacao_recursos')

    return (
        <div className="dsecs">
            <DashSection
                index={1}
                eyebrow="Recursal"
                title="Estoque e extintos"
                subtitle="Indicadores da fase recursal e as saídas em 2º grau no período."
            >
                <div className="grid grid-stat-3">
                    <HeroStat
                        label="Total em recursal"
                        icon="scale"
                        tone="accent"
                        value={valor(r.totalRecursal, fmt.int)}
                        hint="Processos hoje na fase Recursal (ID_FASE = 8), sem período; segue os filtros da página."
                        footer={<FootRow left="Processos na fase recursal" right={<Pill>agora</Pill>} />}
                    />
                    <HeroStat
                        label="Total de entrada em recursal"
                        icon="inbox"
                        tone="info"
                        value={valor(r.entrada, fmt.int)}
                        hint="Processos da fase Recursal com DT_ENTRADA_RECURSAL no período."
                        footer={<FootRow left="Entraram no período" right={<Pill tone="info">período</Pill>} />}
                    />
                    <HeroStat
                        label="Valor dos acórdãos em recursal"
                        icon="dollar"
                        tone="ok"
                        value={valor(r.valorAcordao, fmt.brl)}
                        hint='Soma do VALOR_CAUSA_ACORDO dos processos hoje na fase Recursal. Na v1 o card se chamava "Valor entrada acórdão Recursal", mas mostrava este número (todo o estoque, sem o período).'
                        footer={<FootRow left="Estoque da fase recursal" right={<Pill tone="ok">agora</Pill>} />}
                    />
                </div>
                <div className="grid dist-grid ex-mt">
                    <ChartCard
                        className="ex-rolagem"
                        title="Recursal por subfases"
                        subtitle={`${fmt.int(sub.subfase.length)} subfase(s) · total ${sub.total === null ? '—' : fmt.int(sub.total)} · clique para filtrar`}
                        action={
                            <Segmented
                                label="Base das subfases"
                                options={BASES}
                                value={baseSubfase}
                                onChange={setBaseSubfase}
                            />
                        }
                    >
                        <BarList
                            items={sub.subfase}
                            showShare
                            wrapNames
                            selected={marcados('subfase_recursal')}
                            onSelect={alternar && ((v) => alternar('subfase_recursal', v))}
                            selectLabel="Filtrar pela subfase"
                        />
                    </ChartCard>
                    <Extintos
                        r={r}
                        filtros={marcados('extinto_2g_recursal')}
                        onSelect={alternar && ((v) => alternar('extinto_2g_recursal', v))}
                    />
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Distribuição"
                title="Decisões 1º e 2º grau"
                subtitle="Cruzamento sentença × acórdão (acórdãos no período) e os status de 1º e 2º grau · clique para filtrar."
                action={
                    <button type="button" className="btn" onClick={() => setMatrizAberta(true)}>
                        <Icon name="grid" size={15} /> Matriz de classificação
                    </button>
                }
            >
                <div className="grid ex-ind">
                    {DECISOES.slice(0, 4).map((d) => (
                        <CartaoDecisao
                            key={d.key}
                            d={r.decisoes.itens.find((x) => x.key === d.key)!}
                            filtros={filters}
                            alternar={alternar}
                        />
                    ))}
                    <HeroStat
                        className="ex-ind-alto"
                        label="Total de decisões"
                        icon="scale"
                        tone="neutral"
                        value={valor(r.decisoes.total, fmt.int)}
                        hint="Processos com mérito em 1º e 2º grau classificáveis e acórdão no período, com os filtros da página (menos o de decisão)."
                    />
                    {DECISOES.slice(4).map((d) => (
                        <CartaoDecisao
                            key={d.key}
                            d={r.decisoes.itens.find((x) => x.key === d.key)!}
                            filtros={filters}
                            alternar={alternar}
                        />
                    ))}
                </div>
                <div className="grid ex-duo ex-mt">
                    {(
                        [
                            ['1º grau', 'Sentenças no período', r.status1g, 'id_1g_recursal'],
                            ['2º grau', 'Acórdãos no período', r.status2g, 'id_2g_recursal'],
                        ] as const
                    ).map(([titulo, sub2, itens, key]) => (
                        <ChartCard
                            key={key}
                            className="ex-rolagem"
                            title={`Status ${titulo}`}
                            subtitle={`${sub2} · total ${fmt.int(itens.reduce((t, l) => t + l.value, 0))} · clique para filtrar`}
                        >
                            <BarList
                                items={itens}
                                showShare
                                wrapNames
                                selected={statusSelecionados(itens, key)}
                                onSelect={alternar && clicarStatus(itens, key)}
                                selectLabel="Filtrar pelo status"
                            />
                        </ChartCard>
                    ))}
                </div>
                <div className="grid ex-duo ex-mt">
                    <RankingMagistrados
                        titulo="Ranking de juízes"
                        sub="Taxa de sucesso por juiz (sentenças no período)"
                        itens={r.juizes}
                        selecionados={marcados('juiz_recursal')}
                        onSelect={alternar && ((v) => alternar('juiz_recursal', v))}
                    />
                    <RankingMagistrados
                        titulo="Ranking de relatores"
                        sub="Taxa de sucesso por relator (acórdãos no período)"
                        itens={r.relatores}
                        selecionados={marcados('relator_recursal')}
                        onSelect={alternar && ((v) => alternar('relator_recursal', v))}
                    />
                </div>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Distribuição"
                title="Matérias, competência e vara"
                subtitle={
                    baseDist === 'estoque'
                        ? 'Distribuição do estoque na fase recursal.'
                        : 'Processos com entrada na fase recursal no período.'
                }
                action={
                    <Segmented label="Base da distribuição" options={BASES} value={baseDist} onChange={setBaseDist} />
                }
            >
                <div className="grid tk-tres">
                    <ChartCard
                        className="rc-pizza"
                        title="Recursal por matéria"
                        subtitle={`${dist.total === null ? '—' : fmt.int(dist.total)} processos · clique na fatia para filtrar`}
                    >
                        {dist.materia.length === 0 ? (
                            <ChartEmpty>Sem dados para o filtro atual.</ChartEmpty>
                        ) : (
                            <PieChart
                                items={dist.materia}
                                size={240}
                                max={8}
                                labels
                                labelsTwoLines
                                legendWhenNarrow
                                selected={marcados('materia_recursal')}
                                onSelect={alternar && ((v) => v !== 'Outras' && alternar('materia_recursal', v))}
                                selectLabel="Filtrar pela matéria"
                            />
                        )}
                    </ChartCard>
                    <ChartCard className="ex-rolagem" title="Recursal por competência" subtitle="Clique para filtrar">
                        <BarList
                            items={dist.competencia}
                            showShare
                            wrapNames
                            selected={marcados('competencia_recursal')}
                            onSelect={alternar && ((v) => alternar('competencia_recursal', v))}
                            selectLabel="Filtrar pela competência"
                        />
                    </ChartCard>
                    <ChartCard
                        className="rc-pizza"
                        title="Recursal por vara"
                        subtitle={`${fmt.int(dist.vara.length)} vara(s) · clique na fatia para filtrar`}
                    >
                        {dist.vara.length === 0 ? (
                            <ChartEmpty>Sem dados para o filtro atual.</ChartEmpty>
                        ) : (
                            <PieChart
                                items={dist.vara}
                                size={240}
                                max={8}
                                labels
                                labelsTwoLines
                                legendWhenNarrow
                                selected={marcados('vara_recursal')}
                                onSelect={alternar && ((v) => v !== 'Outras' && alternar('vara_recursal', v))}
                                selectLabel="Filtrar pela vara"
                            />
                        )}
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={4}
                eyebrow="Setor Recursos"
                title="Atividades no período"
                subtitle="Agendamentos do setor RECURSOS · clique nos cards e gráficos para filtrar (os filtros de atividades também recortam os processos da página)."
                action={<Segmented label="Visão das atividades" options={VISOES} value={visao} onChange={setVisao} />}
            >
                <div className={`grid ex-kpis${cardsAtividade.length === 6 ? ' rc-kpis-6' : ''}`}>
                    {cardsAtividade.map((c) => {
                        const clicavel = ['em_andamento', 'vencidas', 'vencem_hoje', 'concluidas'].includes(c.key)
                        const card = (
                            <MiniStat
                                label={c.label}
                                icon={c.icon}
                                tone={c.tone}
                                value={c.v === null ? '—' : fmt.int(c.v)}
                                below={<span className="muted small">{c.nota}</span>}
                            />
                        )
                        return clicavel && alternar ? (
                            <CardFiltro
                                key={c.key}
                                ativo={situacoes.includes(c.key)}
                                onClick={() => alternar('situacao_recursos', c.key)}
                                rotuloAcao={`${c.label}: ${fmt.int(c.v ?? 0)}. Filtrar pela situação`}
                            >
                                {card}
                            </CardFiltro>
                        ) : (
                            <div key={c.key}>{card}</div>
                        )
                    })}
                </div>
                <div className={`grid ex-mt ${r.provimento ? 'rc-ativ' : 'dist-grid'}`}>
                    {r.provimento && (
                        <ChartCard
                            title="Meta de provimento mensal"
                            subtitle={`${fmt.int(r.provimento.qtd)} / ${fmt.int(r.provimento.meta)} processos providos no período`}
                            tag={r.provimento.pct >= 100 ? <Pill tone="warn">Meta atingida</Pill> : undefined}
                        >
                            <GaugeChart
                                value={Math.min(r.provimento.pct, 100)}
                                color={
                                    r.provimento.pct >= 100
                                        ? 'var(--warn-dot)'
                                        : r.provimento.pct >= 70
                                          ? 'var(--accent)'
                                          : 'var(--danger)'
                                }
                                marker={70}
                                caption={`${pct(r.provimento.pct)} da meta`}
                            />
                        </ChartCard>
                    )}
                    <ChartCard
                        className="ex-rolagem"
                        title="Por atividade"
                        subtitle={`${fmt.int(r.porAtividade.length)} atividade(s) · processos com agendamento no período`}
                    >
                        <BarList
                            items={r.porAtividade}
                            showShare
                            wrapNames
                            selected={marcados('atividade_recursos')}
                            onSelect={alternar && ((v) => alternar('atividade_recursos', v))}
                            selectLabel="Filtrar pela atividade"
                        />
                    </ChartCard>
                    <ChartCard
                        className="ex-rolagem"
                        title="Demandas por funcionário"
                        subtitle="Encerradas no período, cumpridas e não cumpridas · clique para filtrar"
                        footer={
                            atribuicao && (
                                <div className="foot-row">
                                    <span>
                                        {um}: <strong className="num">{fmt.int(atribuicao.atribuidas)}</strong>{' '}
                                        atribuídas
                                    </span>
                                    <span className="num">
                                        {fmt.int(atribuicao.porOutros)} encerradas por outra pessoa
                                    </span>
                                </div>
                            )
                        }
                    >
                        <StackedBars
                            rows={r.demandas.map((f) => ({ name: f.name, values: [f.cumpridas, f.naoCumpridas] }))}
                            parts={[
                                { label: 'Encerrado Cumprido', color: 'var(--chart-1)' },
                                { label: 'Encerrado Não Cumprido', color: 'var(--danger)' },
                            ]}
                            selected={funcionarios}
                            onSelect={alternar && ((v) => alternar('funcionario_recursos', v))}
                            selectLabel="Filtrar pelo funcionário"
                        />
                    </ChartCard>
                </div>
                <div className="grid prod-grid ex-mt">
                    <ProducaoDiaria
                        dias={producaoDias(data.producao, funcionarios)}
                        porPrazo={false}
                        setorNome="Recursal"
                        funcionarios={funcionarios}
                    />
                    <ChartCard
                        className="ex-rolagem"
                        title="Média resolvidos por funcionário"
                        subtitle="Cumpridas por dia com conclusão, no período"
                    >
                        <BarList items={r.media} format={fmt.dec2} valueOutside wrapNames />
                    </ChartCard>
                </div>
                <div className="ex-mt">
                    <ListaTarefas
                        tarefas={r.lista}
                        filtrada={[
                            'funcionario_recursos',
                            'atividade_recursos',
                            'status_recursos',
                            'situacao_recursos',
                        ].some((key) => marcados(key as keyof DashboardFilters).length > 0)}
                    />
                </div>
            </DashSection>

            {matrizAberta && <MatrizModal filtros={filters} onSet={set} onClose={() => setMatrizAberta(false)} />}
        </div>
    )
}

function CartaoDecisao({
    d,
    filtros,
    alternar,
}: {
    d: { key: (typeof DECISOES)[number]['key']; label: string; tone: Tone; qtd: number; pct: number }
    filtros: DashboardFilters
    alternar?: (key: keyof DashboardFilters, v: string) => void
}) {
    const valorFiltro = filtroDecisao(d.key)
    const card = (
        <HeroStat
            label={d.label}
            icon={
                d.tone === 'ok'
                    ? 'check-circle'
                    : d.tone === 'danger'
                      ? 'x-circle'
                      : d.tone === 'info'
                        ? 'flow'
                        : 'alert'
            }
            tone={d.tone}
            value={<CountUp value={d.qtd} format={fmt.int} />}
            below={<span className="muted small">{pct(d.pct)} das decisões</span>}
        />
    )
    if (!alternar) return card
    return (
        <CardFiltro
            ativo={(filtros.decisao_recursal ?? []).includes(valorFiltro)}
            onClick={() => alternar('decisao_recursal', valorFiltro)}
            rotuloAcao={`${d.label}: ${fmt.int(d.qtd)}. Filtrar pela decisão`}
        >
            {card}
        </CardFiltro>
    )
}

// O painel "Extintos · 2º grau" da v1: com e sem mérito (clicáveis), a taxa de provimento e os com mérito por tipo.
function Extintos({
    r,
    filtros,
    onSelect,
}: {
    r: ReturnType<typeof lerRecursal>
    filtros: string[]
    onSelect?: (v: string) => void
}) {
    const e = r.extintos
    const cartao = (id: string, rotulo: string, qtd: number | null, valorCausa: number | null, tone: Tone) => {
        const conteudo = (
            <MiniStat
                label={rotulo}
                icon={tone === 'ok' ? 'check-circle' : 'x-circle'}
                tone={tone}
                value={qtd === null ? '—' : fmt.int(qtd)}
                below={
                    <span className="muted small">{valorCausa === null ? '—' : fmt.brl(valorCausa)} em acórdãos</span>
                }
            />
        )
        return onSelect ? (
            <CardFiltro
                key={id}
                ativo={filtros.includes(id)}
                onClick={() => onSelect(id)}
                rotuloAcao={`${rotulo}: filtrar a página`}
            >
                {conteudo}
            </CardFiltro>
        ) : (
            <div key={id}>{conteudo}</div>
        )
    }
    return (
        <ChartCard
            title="Extintos · 2º grau"
            subtitle={
                e.seguemFiltros
                    ? 'Saem após a fase Recursal (acórdãos no período) · clique para filtrar'
                    : 'Saem após a fase Recursal (acórdãos no período, sem os filtros da página, como na v1) · clique para filtrar'
            }
            tag={
                <>
                    {e.taxa !== null && <Pill tone="info">Taxa de provimento {pct(e.taxa)}</Pill>}
                    <Pill>{fmt.int(e.total)} no total</Pill>
                </>
            }
        >
            <div className="grid ex-duo">
                {cartao('com_merito', 'Extintos com mérito', e.comMerito, e.valorComMerito, 'ok')}
                {cartao('sem_merito', 'Extintos sem mérito', e.semMerito, e.valorSemMerito, 'danger')}
            </div>
            {e.porTipo.length > 0 && (
                <div className="rc-portipo">
                    <span className="muted small">Por tipo de acórdão · extintos com mérito</span>
                    <ul role="list">
                        {e.porTipo.map((t) => (
                            <li key={t.tipo}>
                                <span>{t.tipo}</span>
                                <span className="num">
                                    <strong>{fmt.int(t.qtd)}</strong>
                                    {t.valor !== null && <span className="muted"> · {fmt.brl(t.valor)}</span>}
                                </span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </ChartCard>
    )
}

// Ranking de juízes / relatores da v1: casos, taxa de sucesso (cor) e a barra favorável / desfavorável / outros.
function RankingMagistrados({
    titulo,
    sub,
    itens,
    selecionados,
    onSelect,
}: {
    titulo: string
    sub: string
    itens: Magistrado[]
    selecionados: string[]
    onSelect?: (nome: string) => void
}) {
    const marcado = (n: string) => selecionados.some((s) => s.toLowerCase() === n.toLowerCase())
    return (
        <ChartCard
            className="ex-rolagem"
            title={titulo}
            subtitle={`${sub} · clique para filtrar`}
            footer={
                <div className="rc-legenda">
                    <span>
                        <i className="rc-fav" /> Favorável
                    </span>
                    <span>
                        <i className="rc-des" /> Desfavorável
                    </span>
                    <span>
                        <i className="rc-out" /> Outros
                    </span>
                </div>
            }
        >
            {itens.length === 0 ? (
                <ChartEmpty>Nenhum registro no período selecionado.</ChartEmpty>
            ) : (
                <ul className="rc-ranking" role="list">
                    {itens.map((m) => (
                        <li key={m.name} className={selecionados.length > 0 && !marcado(m.name) ? 'dim' : undefined}>
                            <button
                                type="button"
                                disabled={!onSelect}
                                aria-pressed={marcado(m.name)}
                                onClick={() => onSelect?.(m.name)}
                                title={`${m.name}: ${m.fav} favorável(is), ${m.des} desfavorável(is), ${m.outros} outro(s)`}
                            >
                                <span className="tk-ini">{m.initials}</span>
                                <span className="rc-nome">
                                    <strong>{m.name}</strong>
                                    <span className="muted small">{fmt.int(m.total)} caso(s)</span>
                                </span>
                                <Pill tone={tomTaxa(m.taxa)}>{pct(m.taxa)}</Pill>
                                <span className="rc-barra" aria-hidden="true">
                                    <span className="rc-fav" style={{ width: `${m.pFav}%` }} />
                                    <span className="rc-des" style={{ width: `${m.pDes}%` }} />
                                    <span className="rc-out" style={{ width: `${m.pOutros}%` }} />
                                </span>
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </ChartCard>
    )
}

const TOM_DECISAO: Record<string, Tone> = Object.fromEntries(DECISOES.map((d) => [d.key, d.tone]))
const ROTULO_DECISAO: Record<string, string> = Object.fromEntries(DECISOES.map((d) => [d.key, d.label]))

// A matriz de classificação da v1 (1º grau × 2º grau): clicar numa célula filtra a página pela decisão dela e pelos
// status de 1º e 2º grau da linha e da coluna; de novo, tira o filtro.
function MatrizModal({
    filtros,
    onSet,
    onClose,
}: {
    filtros: DashboardFilters
    onSet?: (f: DashboardFilters) => void
    onClose: () => void
}) {
    return (
        <Modal
            title="Matriz de classificação"
            subtitle="Resultado: 1º grau × 2º grau"
            description="Cruzamento sentença × acórdão → classificação final. Clique numa célula para filtrar a página."
            className="ex-modal rc-matriz-modal"
            onClose={onClose}
        >
            <div className="rc-matriz-wrap">
                <table className="rc-matriz">
                    <thead>
                        <tr>
                            <th className="muted small">1º grau ↓ / 2º grau →</th>
                            {MATRIZ_2G.map((c) => (
                                <th key={c}>{c}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {MATRIZ.map((linha, i) => (
                            <tr key={MATRIZ_1G[i]}>
                                <th>{MATRIZ_1G[i]}</th>
                                {linha.map((dec, j) => {
                                    const marcada = celulaMarcada(filtros, i, j)
                                    return (
                                        <td key={j}>
                                            <button
                                                type="button"
                                                className={`rc-celula tone-${TOM_DECISAO[dec]}${marcada ? ' on' : ''}`}
                                                aria-pressed={marcada}
                                                disabled={!onSet}
                                                title={`${MATRIZ_1G[i]} × ${MATRIZ_2G[j]} → ${ROTULO_DECISAO[dec]}`}
                                                onClick={() => onSet?.(clicarCelula(filtros, i, j))}
                                            >
                                                {ROTULO_DECISAO[dec]}
                                            </button>
                                        </td>
                                    )
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className="rc-legenda">
                <span>
                    <i className="rc-fav" /> Ganho mantido, ampliado ou revertido
                </span>
                <span>
                    <i className="rc-des" /> Perda mantida ou revertida
                </span>
                <span>
                    <i className="rc-warn" /> Ganho reduzido / extinção (permite reajuizar)
                </span>
                <span>
                    <i className="rc-info" /> Instrução retomada
                </span>
            </div>
        </Modal>
    )
}
