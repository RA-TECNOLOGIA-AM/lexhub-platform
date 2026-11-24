import { useState } from 'react'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { ColumnChart } from '../../../components/charts/ColumnChart.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat, MiniStat, Pill } from '../../../components/dashboard/StatCard.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { pickSingle } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import type { ContentProps } from '../types.ts'
import { CORES_ANO, MESES, mesNome } from '../setor/datas.ts'
import {
    META_TAXA_RESOLUCAO,
    SLA_HORAS,
    abasDoFeed,
    duracaoHoras,
    iniciais,
    filtrarFeed,
    lerTickets,
    pct,
    porAno,
    type Atividade,
    type TicketsResponse,
} from './tickets.ts'

const VS = ' vs mês anterior'
const valor = (v: number) => <CountUp value={v} format={fmt.int} />
const doTotal = (parte: number, total: number) => `${fmt.pct(pct(parte, total))} do total`

// Tickets (banco NG): as seções da página da v1 (NG/Tickets.tsx) no layout da V2. Clicar nos gráficos filtra a
// página por servidor, categoria e subcategoria (um valor de cada, como na v1).
export function TicketsContent({ data, filters = {}, onFiltersChange }: ContentProps<TicketsResponse>) {
    const t = lerTickets(data)
    const escolher =
        onFiltersChange && ((key: keyof DashboardFilters, v: string) => onFiltersChange(pickSingle(filters, key, v)))
    const servidor = filters.ticket_servidor ?? []
    const { anos, pico } = porAno(t.porMes)
    const listaAnos = [...anos.keys()]
    const [hoje] = useState(() => new Date())
    const anoAtual = String(hoje.getFullYear())
    const somaAbertos = t.abertosPorServidor.reduce((s, p) => s + p.value, 0)
    const somaEncerrados = t.encerradosPorServidor.reduce((s, p) => s + p.value, 0)
    const top5 = t.mediaPorColaborador.slice(0, 5) // a v1 mostrava os 5 primeiros; a média é da equipe toda

    return (
        <div className="dsecs">
            <DashSection
                index={1}
                eyebrow="Visão geral"
                title="Indicadores do período"
                subtitle="Estado atual dos tickets criados no período e a performance de resolução."
            >
                <div className="grid grid-stat">
                    <HeroStat
                        label="Total de tickets"
                        icon="inbox"
                        tone="accent"
                        value={valor(t.total)}
                        below={<DeltaPill value={t.variacao} suffix={VS} plain />}
                        hint='Tickets com status diferente de "Reprovado" criados no período: a base da taxa de resolução e dos percentuais da seção. O comparativo usa o mesmo recorte de dias do mês anterior.'
                        footer={
                            <FootRow
                                left="Mês anterior"
                                right={
                                    <strong className="num">{t.anterior === null ? '—' : fmt.int(t.anterior)}</strong>
                                }
                            />
                        }
                    />
                    <HeroStat
                        label="Aguardando atendimento"
                        icon="clock"
                        tone="warn"
                        value={valor(t.aguardando)}
                        hint='Tickets válidos com status "Em análise": abertos, mas ainda sem atendente.'
                        footer={
                            <FootRow
                                left={doTotal(t.aguardando, t.total)}
                                right={
                                    <Pill tone={t.aguardando > 0 ? 'warn' : 'ok'}>
                                        {t.aguardando > 0 ? 'fila ativa' : 'fila vazia'}
                                    </Pill>
                                }
                            />
                        }
                    />
                    <HeroStat
                        label="Em atendimento"
                        icon="users"
                        tone="info"
                        value={valor(t.emAtendimento)}
                        hint='Tickets válidos com status "Em atendimento": assumidos por um atendente e ainda não encerrados.'
                        footer={
                            <FootRow
                                left={doTotal(t.emAtendimento, t.total)}
                                right={<Pill tone="info">em tratativa</Pill>}
                            />
                        }
                    />
                    <HeroStat
                        label="Encerrados"
                        icon="check-circle"
                        tone="ok"
                        value={valor(t.encerrados)}
                        hint='Tickets válidos com status "Resolvido": o numerador da taxa de resolução.'
                        footer={
                            <FootRow left={doTotal(t.encerrados, t.total)} right={<Pill tone="ok">concluídos</Pill>} />
                        }
                    />
                </div>
                <div className="grid grid-stat ex-mt">
                    <MiniStat
                        label="Cancelados"
                        icon="x-circle"
                        tone="neutral"
                        value={fmt.int(t.cancelados)}
                        below={<span className="muted small">{doTotal(t.cancelados, t.total)}</span>}
                        hint='Tickets válidos com status "Cancelado": abertos e cancelados sem chegar a uma resolução.'
                    />
                    <MiniStat
                        label="Reprovados"
                        icon="ban"
                        tone="danger"
                        value={fmt.int(t.reprovados)}
                        below={
                            <span className="muted small">
                                {fmt.pct(pct(t.reprovados, t.total))} sobre o total válido
                            </span>
                        }
                        hint='Tickets com status "Reprovado" (duplicados, fora do escopo): ficam fora do total e das outras contagens.'
                    />
                    <MiniStat
                        label="Duração média"
                        icon="clock"
                        tone="info"
                        value={duracaoHoras(t.duracao)}
                        below={
                            <Pill tone={t.dentroSla ? 'ok' : 'danger'}>
                                {t.dentroSla ? 'Dentro' : 'Acima'} do SLA de {SLA_HORAS}h
                            </Pill>
                        }
                        hint="Média entre a criação e a última atualização de todos os tickets válidos com essa diferença positiva (não só os encerrados)."
                    />
                    <MiniStat
                        label="Taxa de resolução"
                        icon="target"
                        tone={t.taxa >= META_TAXA_RESOLUCAO ? 'ok' : 'warn'}
                        value={`${fmt.dec1(t.taxa)}%`}
                        below={
                            <span className="tk-barra" aria-hidden="true">
                                <span style={{ width: `${Math.min(100, t.taxa)}%` }} />
                                <i style={{ left: `${META_TAXA_RESOLUCAO}%` }} />
                            </span>
                        }
                        extra={<span className="muted small">meta {META_TAXA_RESOLUCAO}%</span>}
                        hint={`Encerrados ÷ total de tickets × 100. O traço na barra marca a meta de ${META_TAXA_RESOLUCAO}%.`}
                    />
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Distribuição"
                title="Por servidor e categoria"
                subtitle="Clique numa barra ou fatia para filtrar a página (de novo, para tirar o filtro)."
            >
                <div className="grid tk-tres">
                    <ChartCard
                        title="Em aberto por servidor"
                        subtitle='Status "Em atendimento"'
                        tag={<Pill tone="accent">{fmt.int(somaAbertos)} em tratativa</Pill>}
                        footer={<p className="tk-dica">Clique na coluna para filtrar pelo servidor</p>}
                    >
                        <ListaOuVazio vazio="Nenhum ticket em atendimento." itens={t.abertosPorServidor}>
                            <ColumnChart
                                height={240}
                                axis={false}
                                gradient
                                categories={t.abertosPorServidor.map((p) => p.name)}
                                series={[
                                    {
                                        label: 'Em aberto',
                                        color: 'var(--chart-brand)',
                                        values: t.abertosPorServidor.map((p) => p.value),
                                    },
                                ]}
                                selected={servidor}
                                onSelect={escolher && ((v) => escolher('ticket_servidor', v))}
                                selectLabel="Filtrar pelo servidor"
                            />
                        </ListaOuVazio>
                    </ChartCard>
                    <ChartCard
                        title="Tickets por categoria"
                        subtitle={`${fmt.int(t.porCategoria.length)} categoria(s) no período`}
                    >
                        {t.porCategoria.length === 0 ? (
                            <ChartEmpty>Sem tickets no período.</ChartEmpty>
                        ) : (
                            <PieChart
                                items={t.porCategoria}
                                size={240}
                                max={7}
                                labels
                                labelsTwoLines
                                legendWhenNarrow
                                centerLabel="tickets"
                                selected={filters.ticket_categoria}
                                onSelect={escolher && ((v) => v !== 'Outras' && escolher('ticket_categoria', v))}
                                selectLabel="Filtrar pela categoria"
                            />
                        )}
                    </ChartCard>
                    <ChartCard
                        title="Encerrados por servidor"
                        subtitle='Status "Resolvido"'
                        tag={<Pill tone="ok">{fmt.int(somaEncerrados)} concluídos</Pill>}
                        footer={<p className="tk-dica">Clique na coluna para filtrar pelo servidor</p>}
                    >
                        <ListaOuVazio vazio="Nenhum ticket encerrado no período." itens={t.encerradosPorServidor}>
                            <ColumnChart
                                height={240}
                                axis={false}
                                gradient
                                categories={t.encerradosPorServidor.map((p) => p.name)}
                                series={[
                                    {
                                        label: 'Encerrados',
                                        color: 'var(--ok-dot)',
                                        values: t.encerradosPorServidor.map((p) => p.value),
                                    },
                                ]}
                                selected={servidor}
                                onSelect={escolher && ((v) => escolher('ticket_servidor', v))}
                                selectLabel="Filtrar pelo servidor"
                            />
                        </ListaOuVazio>
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Rankings"
                title="Desempenho por colaborador"
                subtitle="Quem mais abre e quem mais encerra tickets, e as subcategorias do período."
            >
                <div className="grid tk-tres">
                    <ChartCard
                        title="Ranking de abertura"
                        action={<span className="muted small">Top 5 solicitantes</span>}
                    >
                        <ListaOuVazio vazio="Sem tickets no período." itens={t.abertura}>
                            <Ranking itens={t.abertura} base={t.total} />
                        </ListaOuVazio>
                    </ChartCard>
                    <ChartCard
                        title="Subcategorias"
                        subtitle="Clique numa fatia para filtrar a página"
                        footer={
                            t.pctSemSubcategoria >= 50 ? (
                                <p className="tk-aviso">
                                    <Icon name="alert" size={15} />
                                    {fmt.pct(t.pctSemSubcategoria)} dos tickets estão sem subcategoria: a classificação
                                    está incompleta.
                                </p>
                            ) : undefined
                        }
                    >
                        {t.subcategorias.length === 0 ? (
                            <ChartEmpty>Sem tickets no período.</ChartEmpty>
                        ) : (
                            <PieChart
                                items={t.subcategorias}
                                size={240}
                                max={7}
                                labels
                                labelsTwoLines
                                legendWhenNarrow
                                centerLabel="tickets"
                                selected={filters.ticket_subcategoria}
                                onSelect={escolher && ((v) => v !== 'Outras' && escolher('ticket_subcategoria', v))}
                                selectLabel="Filtrar pela subcategoria"
                            />
                        )}
                    </ChartCard>
                    <ChartCard
                        title="Ranking de fechamentos"
                        action={<span className="small tone-text-ok">Top 5 resolvedores</span>}
                    >
                        <ListaOuVazio vazio="Nenhum ticket encerrado no período." itens={t.fechamento}>
                            <Ranking itens={t.fechamento} base={t.encerrados} primeiroVerde />
                        </ListaOuVazio>
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={4}
                eyebrow="Evolução"
                title="Tendência ao longo do tempo"
                subtitle="Tickets por mês (todo o histórico, sem o período) e a produtividade média por colaborador."
            >
                <div className="grid dist-grid">
                    <ChartCard
                        title="Tickets por mês"
                        subtitle="Comparado por ano; não depende do período"
                        tag={
                            pico ? (
                                <Pill tone="accent">
                                    Pico: {mesNome(pico.mes)}/{pico.ano} ({fmt.int(pico.valor)})
                                </Pill>
                            ) : undefined
                        }
                    >
                        {listaAnos.length === 0 ? (
                            <ChartEmpty>Sem histórico.</ChartEmpty>
                        ) : (
                            <LineChart
                                height={300}
                                legend
                                emphasizeData
                                labels={MESES}
                                tooltip={{ heading: 'Mês', title: mesNome }}
                                partial={
                                    anos.has(anoAtual)
                                        ? { series: listaAnos.indexOf(anoAtual), index: hoje.getMonth() }
                                        : undefined
                                }
                                series={listaAnos.map((ano, i) => ({
                                    label: ano,
                                    color: CORES_ANO[(listaAnos.length - 1 - i) % CORES_ANO.length],
                                    values: anos.get(ano) ?? [],
                                    dashed: i < listaAnos.length - 1,
                                    area: i === listaAnos.length - 1,
                                }))}
                            />
                        )}
                    </ChartCard>
                    <ChartCard
                        title="Média de encerrados por colaborador"
                        subtitle="Tickets concluídos por dia com movimentação no período"
                        tag={
                            t.mediaPorColaborador.length > 0 ? (
                                <Pill tone="ok">Média da equipe: {fmt.dec2(t.mediaEquipe)}</Pill>
                            ) : undefined
                        }
                        footer={
                            t.mediaPorColaborador.length > 0 ? (
                                <div className="tk-legenda">
                                    <span>
                                        <i className="tk-tracejado" aria-hidden="true" /> Linha tracejada: média da
                                        equipe ({fmt.dec2(t.mediaEquipe)})
                                    </span>
                                    <span>Top {Math.min(5, t.mediaPorColaborador.length)} técnicos</span>
                                </div>
                            ) : undefined
                        }
                    >
                        <ListaOuVazio vazio="Sem encerramentos no período." itens={t.mediaPorColaborador}>
                            <ColumnChart
                                height={280}
                                axis={false}
                                gradient
                                format={fmt.dec2}
                                categories={top5.map((p) => p.name)}
                                series={[
                                    {
                                        label: 'Encerrados por dia',
                                        color: 'var(--chart-brand)',
                                        values: top5.map((p) => p.value),
                                    },
                                ]}
                                colorOf={(i) => (top5[i].value >= t.mediaEquipe ? undefined : 'var(--text-muted)')}
                                reference={{ value: t.mediaEquipe, label: `Média: ${fmt.dec2(t.mediaEquipe)}` }}
                                tooltip
                            />
                        </ListaOuVazio>
                    </ChartCard>
                </div>
            </DashSection>

            {t.atividades.length > 0 && (
                <DashSection
                    index={5}
                    eyebrow="Atividade"
                    title="Últimas movimentações"
                    subtitle="Os 20 tickets do período com atualização mais recente."
                >
                    <Feed atividades={t.atividades} />
                </DashSection>
            )}
        </div>
    )
}

// O ranking da v1 (RankingCard): posição, iniciais, nome, valor e % da base, e a barra embaixo em toda a largura.
// No de fechamentos o 1º fica verde.
function Ranking({
    itens,
    base,
    primeiroVerde = false,
}: {
    itens: { name: string; value: number }[]
    base: number
    primeiroVerde?: boolean
}) {
    const maior = Math.max(...itens.map((p) => p.value), 1)
    return (
        <ol className="tk-ranking">
            {itens.map((p, i) => {
                const verde = primeiroVerde && i === 0
                return (
                    <li key={p.name} className={verde ? 'tone-ok' : 'tone-accent'}>
                        <span className={`tk-pos${i === 0 ? ' primeiro' : ''}`}>{i + 1}º</span>
                        <span className="tk-ini" aria-hidden="true">
                            {iniciais(p.name)}
                        </span>
                        <span className="tk-nome" title={p.name}>
                            {p.name}
                        </span>
                        <span className="tk-val num">
                            <strong>{fmt.int(p.value)}</strong>{' '}
                            <span className={verde || primeiroVerde ? 'tone-text-ok' : 'muted'}>
                                ({fmt.pct(pct(p.value, base))})
                            </span>
                        </span>
                        <span className={`tk-trilho${verde ? ' verde' : ''}`} aria-hidden="true">
                            <span style={{ width: `${(p.value / maior) * 100}%` }} />
                        </span>
                    </li>
                )
            })}
        </ol>
    )
}

function ListaOuVazio({ itens, vazio, children }: { itens: unknown[]; vazio: string; children: React.ReactNode }) {
    return itens.length === 0 ? <ChartEmpty>{vazio}</ChartEmpty> : <>{children}</>
}

// O tom de cada categoria no feed (v1: tomCategoria).
function tomCategoria(c: string): Tone {
    if (c === 'bug') return 'accent'
    if (c === 'suporte') return 'info'
    if (c === 'acesso') return 'danger'
    if (c === 'dashboard') return 'warn'
    if (c === 'duvida' || c === 'dúvida') return 'ok'
    return 'neutral'
}

// O feed de movimentações da v1 (MovimentacoesFeed): abas por categoria, busca e "ver mais" (5 de início).
function Feed({ atividades }: { atividades: Atividade[] }) {
    const [aba, setAba] = useState('todos')
    const [busca, setBusca] = useState('')
    const [expandido, setExpandido] = useState(false)
    const abas = abasDoFeed(atividades)
    const filtradas = filtrarFeed(atividades, aba, busca)
    const visiveis = expandido ? filtradas : filtradas.slice(0, 5)
    return (
        <ChartCard
            title="Atividade recente"
            action={
                <label className="fmenu-search tk-busca">
                    <Icon name="search" size={16} />
                    <span className="sr-only">Buscar nas movimentações</span>
                    <input
                        type="search"
                        placeholder="Buscar por descrição, autor ou #ID..."
                        value={busca}
                        onChange={(e) => setBusca(e.target.value)}
                    />
                </label>
            }
        >
            <Segmented
                label="Categoria"
                className="tk-abas"
                options={abas.map((a) => ({ value: a.value, label: `${a.label} (${a.total})` }))}
                value={aba}
                onChange={(v) => {
                    setAba(v)
                    setExpandido(false)
                }}
            />
            {visiveis.length === 0 ? (
                <ChartEmpty>Nenhuma movimentação encontrada.</ChartEmpty>
            ) : (
                <ul className="tk-feed">
                    {visiveis.map((a) => (
                        <Item key={a.id} a={a} />
                    ))}
                </ul>
            )}
            {filtradas.length > 5 && (
                <button type="button" className="linkbtn muted tk-mais" onClick={() => setExpandido((v) => !v)}>
                    {expandido ? 'Mostrar menos' : `Ver mais ${filtradas.length - 5}`}
                </button>
            )}
        </ChartCard>
    )
}

function Item({ a }: { a: Atividade }) {
    const resolvido = (a.status ?? '').toLowerCase() === 'resolvido'
    const tom = resolvido ? 'ok' : tomCategoria(a.categoria)
    const [copiado, setCopiado] = useState(false)
    const copiar = async () => {
        if (!a.anydesk) return
        try {
            await navigator.clipboard.writeText(a.anydesk)
            setCopiado(true)
            setTimeout(() => setCopiado(false), 1500)
        } catch {
            setCopiado(false)
        }
    }
    return (
        <li className="tk-item">
            <span className={`tk-ico tone-${tom}`} aria-hidden="true">
                <Icon name={resolvido ? 'check-circle' : 'clock'} size={18} />
            </span>
            <div className="tk-corpo">
                <div className="tk-selos">
                    <Pill tone={tomCategoria(a.categoria)}>{a.categoria.toUpperCase()}</Pill>
                    {a.numero && <Pill tone="info">#{a.numero}</Pill>}
                    {a.servidor && <Pill tone="neutral">{a.servidor}</Pill>}
                    {a.status && <span className="muted small">· {a.status}</span>}
                </div>
                <p className="tk-desc">{a.descricao}</p>
                <p className="muted small tk-quem">
                    <Icon name="users" size={12} /> <span className="num">{a.usuario}</span>
                    {a.quando && <> · {a.quando}</>}
                </p>
            </div>
            {(a.anydesk || a.url) && (
                <div className="tk-acoes">
                    {a.anydesk && (
                        <button type="button" className="btn tk-anydesk" onClick={copiar} title="Copiar o AnyDesk">
                            {copiado ? 'Copiado!' : `AnyDesk: ${a.anydesk}`}
                        </button>
                    )}
                    {a.url && (
                        <a className="btn" href={a.url} target="_blank" rel="noopener noreferrer">
                            Abrir chat <Icon name="maximize" size={13} />
                        </a>
                    )}
                </div>
            )}
        </li>
    )
}
