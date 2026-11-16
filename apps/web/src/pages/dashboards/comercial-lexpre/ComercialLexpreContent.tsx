import { useState } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { ColumnChart } from '../../../components/charts/ColumnChart.tsx'
import { StackedBars } from '../../../components/charts/StackedBars.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat, MiniStat } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { topN } from '../../../lib/charts.ts'
import { pickSingle } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import { isPlaceholder, share } from '../setor/setor.ts'
import { AtendentesTable } from './AtendentesTable.tsx'
import { CaptacaoSection } from './CaptacaoSection.tsx'
import { MetaInteligenteCard } from './MetaInteligenteCard.tsx'
import { MetaPorAtendente } from './MetaPorAtendente.tsx'
import { META_ANUAL, rotuloCanal } from './comercial.ts'
import { MetaAnual } from './MetaAnual.tsx'
import type { ComercialLexpreResponse } from './types.ts'

// As etapas da fila do pré-protocolo (campos da API), com as cores da legenda.
const ETAPAS = [
    { key: 'pendencias', label: 'Pendências', color: 'var(--c-danger)' },
    { key: 'triagem', label: 'Triagem', color: 'var(--chart-5)' },
    { key: 'nao_organizado', label: 'Não organizado', color: 'var(--warn-dot)' },
    { key: 'nao_confeccionado', label: 'Não confeccionado', color: 'var(--chart-4)' },
    { key: 'nao_protocolado', label: 'Não protocolado', color: 'var(--chart-3)' },
    { key: 'protocolado', label: 'Protocolado', color: 'var(--chart-1)' },
] as const

// Comercial (LexPre): as métricas da v1 no layout novo dos dashboards de setor. Carregar, erros, cabeçalho,
// período e filtros ficam no DashboardView; clicar num atendente ou numa rubrica liga o filtro.
export function ComercialLexpreContent({
    data,
    filters = {},
    onToggleFilter,
    onFiltersChange,
}: ContentProps<ComercialLexpreResponse>) {
    const [canalRubrica, setCanalRubrica] = useState('total')
    const s = data.stats
    const porAtendente =
        onToggleFilter && ((name: string) => void (!isPlaceholder(name) && onToggleFilter('atendente_comercial', name)))
    // Rubrica: um valor só (como na v1): outra troca, a mesma desliga.
    const porRubrica = onFiltersChange && ((name: string) => onFiltersChange(pickSingle(filters, 'rubrica', name)))

    const contratos = s.clientes_todos.total
    const rubricas = topN(s.acoes_fechadas_por_rubrica[canalRubrica] ?? [], 100)
    const totalRubricas = rubricas.reduce((sum, p) => sum + p.value, 0)
    const canaisRubrica = Object.keys(s.acoes_fechadas_por_rubrica)
    const referencia = data.meta.to // fim do período da página (a API sempre manda)

    return (
        <div className="dsecs">
            {s.valor_causa_protocolado_ano !== undefined && (
                <MetaAnual
                    lexpre={s.valor_causa_protocolado_ano}
                    legado={data.valor_causa_protocolado_legado ?? null}
                    meta={META_ANUAL}
                    ano={s.ano_meta ?? Number(referencia.slice(0, 4))}
                />
            )}
            <CaptacaoSection stats={s} />

            <DashSection
                index={2}
                eyebrow="Performance"
                title="Leads, ranking e atividade diária"
                subtitle="Funil de leads por campanha e produtividade da equipe."
            >
                {/* Grade da v1: Ranking alto à esquerda, os 4 números de leads (2 × 2) no meio e as atividades
                    de hoje (ações sobre contratos) à direita. */}
                <div className="grid perf-grid grid-mini-stack">
                    <ChartCard
                        className="perf-ranking"
                        title="Ranking de ações fechadas"
                        subtitle="Clique num atendente para filtrar a página"
                    >
                        <BarList
                            items={s.ranking_acoes_fechadas_por_atendente}
                            ranked
                            selected={filters.atendente_comercial}
                            onSelect={porAtendente}
                            selectLabel="Filtrar pelo atendente"
                        />
                    </ChartCard>
                    <MiniStat
                        className="perf-leads-geral"
                        label="Leads geral"
                        icon="users"
                        tone="accent"
                        value={<CountUp value={s.leads_geral.total} format={fmt.int} />}
                        below={<DeltaPill value={s.leads_geral.comparativo} suffix="vs mês anterior" plain />}
                        hint={`Atendimentos (leads) abertos no período, de todos os canais. Viraram contrato: ${fmt.int(contratos)}.`}
                    />
                    <MiniStat
                        className="perf-leads-campanha"
                        label="Leads campanha"
                        icon="target"
                        tone="accent"
                        value={<CountUp value={s.leads_campanha.total} format={fmt.int} />}
                        below={<DeltaPill value={s.leads_campanha.comparativo} suffix="vs mês anterior" plain />}
                        hint={`Leads de campanha abertos no período. Viraram contrato: ${fmt.int(s.clientes_campanha.total)}.`}
                    />
                    <MiniStat
                        className="perf-taxa-geral"
                        label="Taxa de leads geral"
                        icon="percent"
                        tone="ok"
                        value={<CountUp value={s.taxa_leads_geral.total} format={(v) => `${fmt.dec2(v)}%`} />}
                        below={<DeltaPill value={s.taxa_leads_geral.comparativo} suffix="vs mês anterior" plain />}
                        hint="Leads do período que viraram contrato."
                    />
                    <MiniStat
                        className="perf-taxa-campanha"
                        label="Taxa de leads campanha"
                        icon="percent"
                        tone="ok"
                        value={<CountUp value={s.taxa_leads_campanha.total} format={(v) => `${fmt.dec2(v)}%`} />}
                        below={<DeltaPill value={s.taxa_leads_campanha.comparativo} suffix="vs mês anterior" plain />}
                        hint="Leads de campanha do período que viraram contrato."
                    />
                    <ChartCard className="perf-acoes-hoje" title="Ações diárias (por atendente)" subtitle="Hoje">
                        <BarList
                            items={topN(s.acoes_fechadas_hoje_por_atendente, 20)}
                            selected={filters.atendente_comercial}
                            onSelect={porAtendente}
                            selectLabel="Filtrar pelo atendente"
                        />
                    </ChartCard>
                    <ChartCard
                        className="perf-contratos-hoje"
                        title="Contratos diários (por atendente)"
                        subtitle="Hoje"
                    >
                        <BarList
                            items={topN(s.contratos_fechados_hoje_por_atendente, 20)}
                            selected={filters.atendente_comercial}
                            onSelect={porAtendente}
                            selectLabel="Filtrar pelo atendente"
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Protocolos"
                title="Protocolos e valor de causa"
                subtitle="Volume protocolado, ticket médio e tempo até a entrada no fluxo."
            >
                <div className="grid grid-stat">
                    <HeroStat
                        label="Protocolados"
                        icon="check-circle"
                        tone="accent"
                        value={<CountUp value={s.protocolados.total} format={fmt.int} />}
                        below={<DeltaPill value={s.protocolados.comparativo} suffix="vs mês anterior" plain />}
                        hint="Demandas dos contratos protocoladas no período."
                        footer={
                            <FootRow
                                left="Sobre as ações fechadas"
                                right={
                                    <span className="num">
                                        {fmt.dec1(share(s.protocolados.total, s.acoes_fechadas.total))}%
                                    </span>
                                }
                            />
                        }
                    />
                    <HeroStat
                        label="Valor de causa protocolado"
                        icon="dollar"
                        tone="ok"
                        value={<CountUp value={s.valor_causa_protocolado.total} format={fmt.brl} />}
                        below={
                            <DeltaPill value={s.valor_causa_protocolado.comparativo} suffix="vs mês anterior" plain />
                        }
                        hint="Soma do valor de causa das demandas protocoladas no período (ANP usa o dano moral)."
                        footer={
                            <FootRow
                                left="Volume financeiro"
                                right={<span className="tone-text-ok">{data.meta.unit}</span>}
                            />
                        }
                    />
                    <HeroStat
                        label="Ticket médio protocolado"
                        icon="receipt"
                        tone="info"
                        value={<CountUp value={s.ticket_medio_protocolado.total} format={fmt.brl} />}
                        below={
                            <DeltaPill value={s.ticket_medio_protocolado.comparativo} suffix="vs mês anterior" plain />
                        }
                        hint="Valor de causa protocolado dividido pelos protocolados do período."
                        footer={<FootRow left="Por demanda protocolada" />}
                    />
                    <HeroStat
                        label="Tempo médio até o protocolo"
                        icon="clock"
                        tone="info"
                        value={<CountUp value={s.tempo_medio_ate_protocolo_horas / 24} format={fmt.duracao} />}
                        hint="Da assinatura do contrato até o protocolo, nas demandas protocoladas no período."
                        footer={<FootRow left="Da assinatura ao protocolo" />}
                    />
                </div>
                <div className="grid dist-grid grid-mini">
                    <ChartCard
                        title="Fila de demandas no pré-protocolo"
                        subtitle="Onde estão hoje as demandas de cada atendente (acumulado)"
                    >
                        <ColumnChart
                            height={360}
                            partValues
                            tooltip
                            categories={s.fila_pre_protocolo_por_atendente.map((f) => f.name)}
                            series={ETAPAS.map((e) => ({
                                label: e.label,
                                color: e.color,
                                values: s.fila_pre_protocolo_por_atendente.map((f) => f[e.key]),
                            }))}
                            selected={filters.atendente_comercial}
                            onSelect={porAtendente}
                            selectLabel="Filtrar pelo atendente"
                        />
                    </ChartCard>
                    <ChartCard title="Valor de causa" subtitle="Por atendente, no período">
                        <StackedBars
                            format={fmt.brl}
                            showTotal={false}
                            parts={[
                                { label: 'Protocolado', color: 'var(--chart-1)' },
                                { label: 'Não protocolado', color: 'var(--chart-3)' },
                            ]}
                            rows={s.valor_causa_por_atendente.map((v) => ({
                                name: v.name,
                                values: [v.protocolado, v.nao_protocolado],
                            }))}
                            selected={filters.atendente_comercial}
                            onSelect={porAtendente}
                            selectLabel="Filtrar pelo atendente"
                        />
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={4}
                eyebrow="Distribuição"
                title="Total de rubricas"
                subtitle="Composição das ações fechadas por rubrica em cada origem. Clique numa rubrica para filtrar a página."
            >
                <ChartCard
                    title="Distribuição por rubrica"
                    subtitle={`${fmt.int(totalRubricas)} ações fechadas · ${rubricas.length} rubricas`}
                    action={
                        <label className="field-select">
                            <span className="sr-only">Origem</span>
                            <select value={canalRubrica} onChange={(e) => setCanalRubrica(e.target.value)}>
                                {canaisRubrica.map((c) => (
                                    <option key={c} value={c}>
                                        {c === 'total' ? 'Total de rubricas' : rotuloCanal(c)}
                                    </option>
                                ))}
                            </select>
                        </label>
                    }
                >
                    <PieChart
                        items={rubricas}
                        centerLabel="ações fechadas"
                        labels
                        selected={filters.rubrica}
                        onSelect={porRubrica}
                        selectLabel="Filtrar pela rubrica"
                    />
                </ChartCard>
            </DashSection>

            <DashSection
                index={5}
                eyebrow="Equipe"
                title="Acompanhamento por atendente"
                subtitle="Desempenho individual contra a meta do período, e leads/clientes/taxa de fechamento por canal. Verde = acima da média do time, vermelho = abaixo."
            >
                <div className="stack">
                    <MetaPorAtendente referencia={referencia} filters={filters} />
                    <MetaInteligenteCard dados={data.meta_inteligente} />
                    <AtendentesTable
                        linhas={s.tabela_por_atendente}
                        totais={s.totais_tabela_por_atendente}
                        filteredTo={filters.atendente_comercial ?? []}
                        onFilterPerson={porAtendente}
                    />
                </div>
            </DashSection>
        </div>
    )
}
