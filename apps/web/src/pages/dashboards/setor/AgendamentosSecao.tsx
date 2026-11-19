import { useState, type ReactNode } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { StackedBars } from '../../../components/charts/StackedBars.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { MiniStat, Pill } from '../../../components/dashboard/StatCard.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import type { IconName } from '../../../components/ui/Icon.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import { ListaTarefas, ProducaoDiaria } from '../execucao/AtividadesSection.tsx'
import { diasDosFuncionarios, type Visao, type VisaoDados } from '../pendencias-intermediarias/intermediarias.ts'

const VISOES: { value: Visao; label: string }[] = [
    { value: 'por_prazo', label: 'Por prazo' },
    { value: 'concluidas', label: 'Concluídas' },
]

// Meta de referência do gráfico de média (fixa na v1).
const META_MEDIA = 16

type Props = {
    eyebrow: string // "Pendências Intermediárias"
    setorNome: string // no título da produção diária
    visoes: Record<Visao, VisaoDados>
    filters: DashboardFilters
    onToggleFilter?: (key: keyof DashboardFilters, value: string) => void
    chaves: { funcionario: keyof DashboardFilters; atividade: keyof DashboardFilters }
    bloco: ReactNode // entre os cards e os gráficos: a dilação (Pendências) ou a agenda/comissão (Emendas)
    textos: {
        emAndamento: string // quais status contam como "em andamento"
        porAtividade: (porPrazo: boolean) => string
        media: (porPrazo: boolean) => string
    }
    coresAtividade?: Record<string, string> // cor por atividade em "Por atividade" (ex.: gera / não gera comissão)
    legendaAtividade?: ReactNode
    outrosFiltros?: number // filtros da página além de funcionário e atividade (ex.: UF): marcam a lista como filtrada
}

// A seção única das páginas da v1 de setor de agendamentos (Pendências Intermediárias, Emendas e Manifestações), no
// layout da V2: a troca Por prazo | Concluídas, os 5 cards, o bloco do setor, a distribuição por atividade e por
// funcionário, a produção "mês a mês" com os dias, a média por funcionário e a lista de tarefas. Cliques nos gráficos
// filtram a página (vão na URL e na API, como os filtros da v1); o histórico segue o filtro de funcionário somando as
// séries de cada um.
export function AgendamentosSecao({
    eyebrow,
    setorNome,
    visoes,
    filters,
    onToggleFilter,
    chaves,
    bloco,
    textos,
    coresAtividade,
    legendaAtividade,
    outrosFiltros = 0,
}: Props) {
    const [visao, setVisao] = useState<Visao>('por_prazo')
    const v = visoes[visao]
    const porPrazo = visao === 'por_prazo'
    const funcionarios = filters[chaves.funcionario] ?? []
    const atividades = filters[chaves.atividade] ?? []
    const alternarFuncionario = onToggleFilter && ((nome: string) => onToggleFilter(chaves.funcionario, nome))
    const alternarAtividade = onToggleFilter && ((nome: string) => onToggleFilter(chaves.atividade, nome))

    const c = v.cards
    const pct = (x: number | null) => (c.total && x !== null ? `${fmt.dec1((x / c.total) * 100)}% do total` : '')
    const cards: { label: string; v: number | null; icon: IconName; tone: Tone; nota: string }[] = [
        {
            label: 'Total de atividades',
            v: c.total,
            icon: 'list',
            tone: 'neutral',
            nota: porPrazo ? 'em aberto com prazo no período' : 'em aberto criadas no período',
        },
        { label: 'Em andamento', v: c.emAndamento, icon: 'flow', tone: 'info', nota: textos.emAndamento },
        { label: 'Vencidas', v: c.vencidas, icon: 'alert', tone: 'danger', nota: pct(c.vencidas) || 'prazo já passou' },
        { label: 'Vencem hoje', v: c.vencemHoje, icon: 'calendar', tone: 'warn', nota: 'prazo no dia atual' },
        {
            label: 'Concluídas',
            v: c.concluidas,
            icon: 'check-circle',
            tone: 'ok',
            nota: porPrazo ? 'encerradas com prazo no período' : 'encerradas no período',
        },
    ]

    // "Atribuição" da v1: com um funcionário só escolhido, quantas são dele e quem encerrou.
    const um = funcionarios.length === 1 ? funcionarios[0] : null
    const atribuicao = um
        ? {
              atribuidas: v.lista.filter((t) => t.responsavel === um).length,
              porOutro: v.lista.filter((t) => t.encerradoPor !== null).length,
          }
        : null

    return (
        <DashSection
            index={1}
            eyebrow={eyebrow}
            title={porPrazo ? 'Atividades e distribuição' : 'Atividades concluídas no período'}
            subtitle={
                porPrazo
                    ? 'Agendamentos do setor classificados pelo prazo · o "mês a mês" é do histórico todo.'
                    : 'Agendamentos do setor pela data de conclusão · clique nos gráficos para filtrar a página.'
            }
            action={<Segmented label="Visão das atividades" options={VISOES} value={visao} onChange={setVisao} />}
        >
            <div className="grid ex-kpis pi-kpis">
                {cards.map((k) => (
                    <MiniStat
                        key={k.label}
                        label={k.label}
                        icon={k.icon}
                        tone={k.tone}
                        value={k.v === null ? '—' : fmt.int(k.v)}
                        below={k.nota ? <span className="muted small">{k.nota}</span> : undefined}
                    />
                ))}
            </div>

            <div className="ex-mt">{bloco}</div>

            <div className="grid dist-grid ex-mt">
                <ChartCard
                    className="ex-rolagem"
                    title="Por atividade"
                    subtitle={textos.porAtividade(porPrazo)}
                    action={legendaAtividade ?? (alternarAtividade && <Pill tone="accent">Clique para filtrar</Pill>)}
                >
                    <BarList
                        items={v.porAtividade}
                        wrapNames
                        showShare
                        colors={coresAtividade}
                        selected={atividades}
                        onSelect={alternarAtividade}
                        selectLabel="Filtrar pela atividade"
                    />
                </ChartCard>
                <ChartCard
                    className="ex-rolagem"
                    title="Demandas por funcionário"
                    subtitle={`Encerradas ${porPrazo ? 'com prazo' : ''} no período, por quem encerrou`}
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
                        rows={v.porFuncionario.map((f) => ({ name: f.name, values: [f.cumpridas, f.naoCumpridas] }))}
                        parts={[
                            { label: 'Encerrado Cumprido', color: 'var(--chart-1)' },
                            { label: 'Encerrado Não Cumprido', color: 'var(--danger)' },
                        ]}
                        selected={funcionarios}
                        onSelect={alternarFuncionario}
                        selectLabel="Filtrar pelo funcionário"
                    />
                </ChartCard>
            </div>

            <div className="grid prod-grid ex-mt">
                <ProducaoDiaria
                    key={`${visao}-${funcionarios.join('|')}`}
                    dias={diasDosFuncionarios(v, funcionarios)}
                    porPrazo={porPrazo}
                    setorNome={setorNome}
                    funcionarios={funcionarios}
                />
                <ChartCard
                    className="ex-rolagem"
                    title={
                        porPrazo ? 'Média de concluídas por funcionário (prazo)' : 'Média de concluídas por funcionário'
                    }
                    subtitle={textos.media(porPrazo)}
                    action={
                        <Pill tone="ok">
                            <span className="legend-dash" aria-hidden="true" /> Meta: {fmt.int(META_MEDIA)}/dia
                        </Pill>
                    }
                >
                    {v.media.length === 0 ? (
                        <ChartEmpty>Sem concluídas.</ChartEmpty>
                    ) : (
                        <BarList
                            items={v.media}
                            format={fmt.dec1}
                            valueOutside
                            wrapNames
                            selected={funcionarios}
                            onSelect={alternarFuncionario}
                            selectLabel="Filtrar pelo funcionário"
                        />
                    )}
                </ChartCard>
            </div>

            <div className="ex-mt">
                <ListaTarefas
                    tarefas={v.lista}
                    filtrada={funcionarios.length + atividades.length + outrosFiltros > 0}
                />
            </div>
        </DashSection>
    )
}
