import { useState } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { StackedBars } from '../../../components/charts/StackedBars.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { MiniStat, Pill } from '../../../components/dashboard/StatCard.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import { DataTable, type Column } from '../../../components/ui/DataTable.tsx'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { Modal } from '../../../components/ui/Modal.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { clearFilter, toggleFilter } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import { diaCurto, diaLongo, MESES } from '../setor/datas.ts'
import { CardFiltro, MesAMes, Paginador } from './partes.tsx'
import { usePagina } from './usePagina.ts'
import {
    CHAVES,
    diasDoMes,
    diasPorMes,
    mesesComDias,
    numeroCnj,
    tomStatus,
    type Atraso,
    type Setor,
    type SetorExecucao,
    type Tarefa,
    type VisaoAtividades,
} from './setorExecucao.ts'

const META_DIARIA = 20 // "Média Resolvidos por Funcionário": a meta de referência da v1

const VISOES: { value: VisaoAtividades; label: string }[] = [
    { value: 'concluidas', label: 'Concluídas' },
    { value: 'por_prazo', label: 'Por prazo' },
]

type Props = {
    index: number
    setor: Setor
    dados: SetorExecucao
    filters: DashboardFilters
    setFilters?: (f: DashboardFilters) => void
}

// Seção "Atividades" das páginas da v1 de Execução (agendamentos do setor no LexFlow), nas visões Concluídas
// (criadas no período) e Por prazo (prazo no período). Os cards, as barras e a lista filtram a seção
// (funcionário, atividade, situação); "Vencidas" abre o detalhamento dos atrasos, como na v1.
export function AtividadesSection({ index, setor, dados, filters, setFilters }: Props) {
    const [visao, setVisao] = useState<VisaoAtividades>('concluidas')
    const [atrasosAberto, setAtrasosAberto] = useState(false)
    const k = CHAVES[setor]
    const a = dados.atividades[visao]
    const porPrazo = visao === 'por_prazo'
    const nomeSetor = setor === 'acordos' ? 'ACORDOS' : 'EXECUÇÃO'

    const marcados = (key: keyof DashboardFilters) => filters[key] ?? []
    const alternar =
        setFilters && ((key: keyof DashboardFilters, v: string) => setFilters(toggleFilter(filters, key, v)))
    const situacoes = marcados(k.situacao)
    const funcionarios = marcados(k.funcionario)
    const atividades = marcados(k.atividade)
    const status = marcados(k.status)

    const pct = (v: number | null) => (a.total && v !== null ? (v / a.total) * 100 : null)
    const cards: { key: string; label: string; v: number | null; icon: IconName; tone: Tone; nota: string }[] = [
        {
            key: 'total',
            label: 'Total de atividades',
            v: a.total,
            icon: 'list',
            tone: 'neutral',
            nota: porPrazo ? 'com prazo no período' : 'criadas no período',
        },
        {
            key: 'em_andamento',
            label: 'Em andamento',
            v: a.emAndamento,
            icon: 'flow',
            tone: 'info',
            nota: 'iniciadas ou reabertas',
        },
        {
            key: 'vencidas',
            label: 'Vencidas',
            v: a.vencidas,
            icon: 'alert',
            tone: 'danger',
            nota:
                pct(a.vencidas) !== null ? `${fmt.dec1(pct(a.vencidas) ?? 0)}% do total · ver atrasos` : 'ver atrasos',
        },
        {
            key: 'vencem_hoje',
            label: 'Vencem hoje',
            v: a.vencemHoje,
            icon: 'calendar',
            tone: 'warn',
            nota: 'prazo no dia atual',
        },
        {
            key: 'concluidas',
            label: 'Concluídas',
            v: a.concluidas,
            icon: 'check-circle',
            tone: 'ok',
            nota: porPrazo ? 'encerradas com prazo no período' : 'encerradas no período',
        },
    ]
    const clicarCard = (key: string) => {
        if (key === 'vencidas') return setAtrasosAberto(true)
        if (!setFilters) return
        if (key === 'total') return setFilters(clearFilter(filters, k.situacao))
        setFilters(toggleFilter(filters, k.situacao, key))
    }

    // As etiquetas dos filtros da seção, com o ✕ para tirar cada uma.
    type Etiqueta = { key: keyof DashboardFilters; v: string; rotulo: string; texto: string }
    const etiqueta =
        (key: keyof DashboardFilters, rotulo: string, texto: (v: string) => string = (v) => v) =>
        (v: string): Etiqueta => ({ key, v, rotulo, texto: texto(v) })
    const etiquetas: Etiqueta[] = [
        ...funcionarios.map(etiqueta(k.funcionario, 'Funcionário')),
        ...atividades.map(etiqueta(k.atividade, 'Atividade')),
        ...situacoes.map(
            etiqueta(k.situacao, 'Situação', (v) => a.opcoes.situacoes.find((s) => s.id === v)?.label ?? v),
        ),
        ...status.map(etiqueta(k.status, 'Status')),
    ]
    const limpar = () => {
        if (!setFilters) return
        let f = filters
        for (const key of [k.funcionario, k.atividade, k.situacao, k.status]) f = clearFilter(f, key)
        setFilters(f)
    }

    // "Atribuição" da v1: com um funcionário só escolhido, quantas foram dele e quem encerrou.
    const um = funcionarios.length === 1 ? funcionarios[0] : null
    const atribuicao = um
        ? {
              atribuidas: a.lista.filter((t) => t.responsavel === um).length,
              porOutro: a.lista.filter((t) => t.encerradoPor !== null).length,
          }
        : null

    return (
        <DashSection
            index={index}
            eyebrow={setor === 'acordos' ? 'Setor Execução de Acordos' : 'Setor Execução'}
            title={porPrazo ? 'Atividades e distribuição' : 'Atividades no período'}
            subtitle={`Agendamentos do setor ${nomeSetor}${porPrazo ? ' classificados pelo prazo' : ''} · clique nos cards e gráficos para filtrar a seção.`}
        >
            <div className="ex-toolbar">
                <Segmented label="Visão das atividades" options={VISOES} value={visao} onChange={setVisao} />
                {etiquetas.length > 0 && (
                    <div className="ex-chips">
                        {etiquetas.map((e) => (
                            <span key={`${String(e.key)}:${e.v}`} className="chip" title={`${e.rotulo}: ${e.texto}`}>
                                {e.rotulo}: {e.texto}
                                <button
                                    type="button"
                                    aria-label={`Tirar o filtro ${e.rotulo}: ${e.texto}`}
                                    onClick={() => alternar?.(e.key, e.v)}
                                >
                                    <Icon name="close" size={12} />
                                </button>
                            </span>
                        ))}
                        <button type="button" className="linkbtn muted" onClick={limpar}>
                            Limpar filtros
                        </button>
                    </div>
                )}
            </div>

            <div className="grid ex-kpis">
                {cards.map((c) => (
                    <CardFiltro
                        key={c.key}
                        ativo={c.key === 'total' || c.key === 'vencidas' ? undefined : situacoes.includes(c.key)}
                        onClick={() => clicarCard(c.key)}
                        rotuloAcao={
                            c.key === 'vencidas'
                                ? `Ver os atrasos das ${fmt.int(c.v ?? 0)} vencidas`
                                : c.key === 'total'
                                  ? `${c.label}: ${fmt.int(c.v ?? 0)}. Mostrar todas as situações`
                                  : `${c.label}: ${fmt.int(c.v ?? 0)}. Filtrar a seção`
                        }
                    >
                        <MiniStat
                            label={c.label}
                            icon={c.icon}
                            tone={c.tone}
                            value={c.v === null ? '—' : fmt.int(c.v)}
                            below={<span className="muted small">{c.nota}</span>}
                        />
                    </CardFiltro>
                ))}
            </div>

            <div className="grid dist-grid ex-mt">
                <ChartCard
                    className="ex-rolagem"
                    title="Por atividade"
                    subtitle="Processos distintos por tipo de atividade do agendamento"
                    action={alternar && <Pill tone="accent">Clique para filtrar</Pill>}
                >
                    <BarList
                        items={a.porAtividade}
                        wrapNames
                        selected={atividades}
                        onSelect={alternar && ((v) => alternar(k.atividade, v))}
                        selectLabel="Filtrar pela atividade"
                    />
                </ChartCard>
                <ChartCard
                    className="ex-rolagem"
                    title="Demandas por funcionário"
                    subtitle="Encerradas no período, cumpridas e não cumpridas"
                    footer={
                        atribuicao && (
                            <div className="foot-row">
                                <span>
                                    {um}: <strong className="num">{fmt.int(atribuicao.atribuidas)}</strong> atribuídas
                                </span>
                                <span className="num">{fmt.int(atribuicao.porOutro)} encerradas por outra pessoa</span>
                            </div>
                        )
                    }
                >
                    <StackedBars
                        rows={a.porFuncionario.map((f) => ({ name: f.name, values: [f.cumpridas, f.naoCumpridas] }))}
                        parts={[
                            { label: 'Encerrado Cumprido', color: 'var(--chart-1)' },
                            { label: 'Encerrado Não Cumprido', color: 'var(--danger)' },
                        ]}
                        selected={funcionarios}
                        onSelect={alternar && ((v) => alternar(k.funcionario, v))}
                        selectLabel="Filtrar pelo funcionário"
                    />
                </ChartCard>
            </div>

            <div className="grid prod-grid ex-mt">
                <ProducaoDiaria
                    dias={a.resolvidosPorDia}
                    porPrazo={porPrazo}
                    setorNome={setor === 'acordos' ? 'Execução de Acordos' : 'Execução'}
                    funcionarios={funcionarios}
                />
                <ChartCard
                    className="ex-rolagem"
                    title="Média resolvidos por funcionário"
                    subtitle="Cumpridas por dia com conclusão, no período"
                    action={
                        <Pill tone="ok">
                            <span className="legend-dash" aria-hidden="true" /> Meta: {fmt.int(META_DIARIA)}/dia
                        </Pill>
                    }
                >
                    <BarList items={a.mediaPorFuncionario} format={fmt.dec1} valueOutside wrapNames />
                </ChartCard>
            </div>

            <div className="ex-mt">
                <ListaTarefas tarefas={a.lista} filtrada={etiquetas.length > 0} />
            </div>

            {atrasosAberto && (
                <AtrasosModal
                    total={dados.atrasos.total}
                    faixas={dados.atrasos.faixas}
                    onClose={() => setAtrasosAberto(false)}
                />
            )}
        </DashSection>
    )
}

// Produção diária da v1: as cumpridas mês a mês (histórico todo); clicar num mês mostra os dias dele. Segue os
// filtros da seção: com um funcionário escolhido (em "Demandas por funcionário"), é a produção só dele.
function ProducaoDiaria({
    dias,
    porPrazo,
    setorNome,
    funcionarios,
}: {
    dias: { name: string; value: number }[]
    porPrazo: boolean
    setorNome: string
    funcionarios: string[]
}) {
    const [mes, setMes] = useState('')
    const ativo = mesesComDias(dias).includes(mes) ? mes : ''
    const doMes = ativo ? diasDoMes(dias, ativo) : []
    const rotuloMes = (m: string) => `${MESES[Number(m.slice(5, 7)) - 1]} de ${m.slice(0, 4)}`
    const quem =
        funcionarios.length === 1
            ? `de ${funcionarios[0]}`
            : funcionarios.length > 1
              ? `de ${funcionarios.length} funcionários`
              : 'do setor'
    return (
        <ChartCard
            title={ativo ? `Produção diária – ${setorNome}` : `Produção diária – ${setorNome} (mês a mês)`}
            subtitle={
                ativo
                    ? `Cumpridas por dia em ${rotuloMes(ativo)}, ${quem}`
                    : `Cumpridas por mês de ${porPrazo ? 'prazo' : 'conclusão'}, ${quem} (histórico todo) · clique num mês para ver os dias${funcionarios.length === 0 ? '; escolha um funcionário em Demandas para ver só a produção dele' : ''}`
            }
            action={
                ativo && (
                    <button type="button" className="btn" onClick={() => setMes('')}>
                        <Icon name="undo" size={15} />
                        Mês a mês
                    </button>
                )
            }
        >
            {dias.length === 0 ? (
                <ChartEmpty>Sem atividades cumpridas no histórico.</ChartEmpty>
            ) : (
                <div key={ativo || 'meses'} className="ex-drill">
                    {ativo ? (
                        <LineChart
                            height={300}
                            area
                            labels={doMes.map((d) => diaCurto(d.name))}
                            tooltip={{ heading: 'Dia', title: (i) => diaLongo(doMes[i]?.name) }}
                            series={[
                                { label: 'Cumpridas', color: 'var(--chart-1)', values: doMes.map((d) => d.value) },
                            ]}
                        />
                    ) : (
                        <MesAMes
                            pontos={diasPorMes(dias)}
                            height={300}
                            onSelectMes={(ano, m) => setMes(`${ano}-${String(m).padStart(2, '0')}`)}
                        />
                    )}
                </div>
            )}
        </ChartCard>
    )
}

const dataCurta = (iso: string | null) => (iso ? diaLongo(iso.slice(0, 10)) : '—')

type ModoLista = 'expandida' | 'compacta'
const MODOS_LISTA: { value: ModoLista; label: string; icon: IconName }[] = [
    { value: 'expandida', label: 'Expandida', icon: 'list' },
    { value: 'compacta', label: 'Compacta', icon: 'menu' },
]
const POR_PAGINA: Record<ModoLista, number> = { expandida: 5, compacta: 10 }

// A lista de tarefas da v1, em dois modos: compacta (uma linha por tarefa, 10 por página; abre assim) e
// expandida (descrição e quem encerrou, 5 por página). Processo e valor aparecem quando a atividade tem.
function ListaTarefas({ tarefas, filtrada }: { tarefas: Tarefa[]; filtrada: boolean }) {
    const [modo, setModo] = useState<ModoLista>('compacta')
    const p = usePagina(tarefas, POR_PAGINA[modo])
    const compacta = modo === 'compacta'
    const temProcesso = tarefas.some((t) => t.processo)
    const temValor = tarefas.some((t) => t.valor !== null)
    const colunas: Column<Tarefa>[] = [
        { header: '#', render: (t) => <span className="num muted">{t.id}</span> },
        {
            header: 'Tarefa',
            render: (t) =>
                compacta ? (
                    <span className="ex-corta" title={t.descricao || t.atividade}>
                        {t.atividade || '—'}
                    </span>
                ) : (
                    <span className="ex-tarefa">
                        <strong>{t.atividade || '—'}</strong>
                        {t.descricao && <span className="muted small">{t.descricao}</span>}
                    </span>
                ),
        },
        { header: 'Status', render: (t) => <Pill tone={tomStatus(t.status)}>{t.status || '—'}</Pill> },
        {
            header: 'Responsável',
            render: (t) =>
                compacta ? (
                    <span className="ex-corta" title={t.encerradoPor ? `encerrado por ${t.encerradoPor}` : undefined}>
                        {t.responsavel || '—'}
                    </span>
                ) : (
                    <span className="ex-tarefa">
                        {t.responsavel || '—'}
                        {t.encerradoPor && <span className="muted small">enc. por {t.encerradoPor}</span>}
                    </span>
                ),
        },
        ...(compacta
            ? []
            : [{ header: 'Setor', render: (t: Tarefa) => <span className="muted">{t.setor || '—'}</span> }]),
        ...(temProcesso
            ? [{ header: 'Nº processo', render: (t: Tarefa) => <span className="num">{numeroCnj(t.processo)}</span> }]
            : []),
        ...(compacta
            ? []
            : [{ header: 'Criado em', render: (t: Tarefa) => <span className="num">{dataCurta(t.criadoEm)}</span> }]),
        {
            header: 'Prazo',
            render: (t) => (
                <span className={`num${t.vencida ? ' tone-text-danger' : t.venceHoje ? ' tone-text-warn' : ''}`}>
                    {dataCurta(t.prazo)}
                </span>
            ),
        },
        ...(temValor
            ? [
                  {
                      header: 'Valor da execução',
                      align: 'right' as const,
                      render: (t: Tarefa) => (t.valor === null ? '—' : fmt.brl(t.valor)),
                  },
              ]
            : []),
    ]
    const inicio = p.pagina * POR_PAGINA[modo]
    return (
        <ChartCard
            title="Lista de atividades"
            subtitle={`${fmt.int(tarefas.length)} tarefa(s)${filtrada ? ' com os filtros da seção' : ''}${
                tarefas.length > 0 ? ` · mostrando ${inicio + 1}–${inicio + p.itens.length}` : ''
            }`}
            action={<Segmented label="Modo da lista" options={MODOS_LISTA} value={modo} onChange={setModo} />}
        >
            <div className={compacta ? 'ex-lista compacta' : 'ex-lista'}>
                <DataTable
                    rows={p.itens}
                    rowKey={(t) => t.id}
                    empty="Nenhuma atividade no período."
                    columns={colunas}
                />
            </div>
            <Paginador pagina={p.pagina} total={p.total} onChange={p.setPagina} />
        </ChartCard>
    )
}

// O detalhamento das vencidas por dias de atraso (o modal da v1, de 1 dia até 6 ou mais).
function AtrasosModal({ total, faixas, onClose }: { total: number; faixas: Atraso[]; onClose: () => void }) {
    return (
        <Modal
            title="Atividades vencidas por dias de atraso"
            subtitle={`${fmt.int(total)} vencida(s) · de 1 dia até 6 dias ou mais`}
            onClose={onClose}
        >
            {faixas.length === 0 ? (
                <ChartEmpty>Nenhuma atividade vencida.</ChartEmpty>
            ) : (
                <ul className="ex-atrasos" role="list">
                    {faixas.map((f) => (
                        <li key={f.dias}>
                            <span className="ex-atrasos-l">
                                <strong>{f.label}</strong>
                                {f.descricao && <span className="muted small">{f.descricao}</span>}
                            </span>
                            <span className="ex-atrasos-bar" aria-hidden="true">
                                <span style={{ width: `${Math.max(2, Math.min(100, f.pct))}%` }} />
                            </span>
                            <span className="num">
                                <strong>{fmt.int(f.quantidade)}</strong>{' '}
                                <span className="muted">({fmt.dec1(f.pct)}%)</span>
                            </span>
                        </li>
                    ))}
                </ul>
            )}
        </Modal>
    )
}
