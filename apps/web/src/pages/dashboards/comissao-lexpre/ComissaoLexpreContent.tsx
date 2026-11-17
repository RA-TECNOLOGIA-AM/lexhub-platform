import { useState } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { FootRow, HeroStat } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { topN } from '../../../lib/charts.ts'
import { pickSingle } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import { isPlaceholder } from '../setor/setor.ts'
import { CaptacaoSection } from '../comercial-lexpre/CaptacaoSection.tsx'
import { rotuloCanal } from '../comercial-lexpre/comercial.ts'
import { linhasValorRubricas, proximaOrdem, type OrdemRubricas } from './comissao.ts'
import type { ComissaoLexpreResponse } from './types.ts'

const brl = (v: number | null) => (v === null ? '—' : fmt.brl(v))

// Comissão Comercial (LexPre): a Captação igual à do Comercial; depois o cálculo da comissão e o detalhamento
// (protocoladas por atendente, valor das rubricas e a pizza). Quem não gere a unidade vê tudo só com os
// próprios dados (a API já manda recortado).
export function ComissaoLexpreContent({
    data,
    filters = {},
    onToggleFilter,
    onFiltersChange,
}: ContentProps<ComissaoLexpreResponse>) {
    const [canal, setCanal] = useState('total')
    const [ordem, setOrdem] = useState<OrdemRubricas>({ key: 'acoes', dir: 'desc' })
    const s = data.stats
    const porAtendente =
        onToggleFilter && ((name: string) => void (!isPlaceholder(name) && onToggleFilter('atendente_comercial', name)))
    const porRubrica = onFiltersChange && ((name: string) => onFiltersChange(pickSingle(filters, 'rubrica', name)))

    const protocoladas = topN(
        Object.entries(s.valor_causa_protocolado_por_atendente_periodo ?? {}).map(([name, value]) => ({
            name,
            value: Number(value) || 0,
        })),
        100,
    )
    const canais = Object.keys(s.acoes_fechadas_por_rubrica)
    const pontos = topN(s.acoes_fechadas_por_rubrica[canal] ?? [], 200)
    const tabela = linhasValorRubricas(pontos, s.rubricas_total_tabela?.[canal] ?? [], ordem)
    const recorte = canal === 'total' ? 'total de rubricas' : rotuloCanal(canal).toLowerCase()
    const desconto = s.desconto_cancelamentos ?? 0

    const seta = (key: OrdemRubricas['key']) =>
        ordem.key === key ? <Icon name={ordem.dir === 'asc' ? 'chevron-up' : 'chevron-down'} size={14} /> : null

    return (
        <div className="dsecs">
            <CaptacaoSection stats={s} />

            <DashSection
                index={2}
                eyebrow="Comissão"
                title="Cálculo e multiplicadores"
                subtitle="Base de comissão, fator multiplicador e proporcionais aplicados no período."
            >
                <div className="grid grid-stat comissao-grid">
                    <HeroStat
                        label="Comissão base"
                        icon="dollar"
                        tone="accent"
                        value={<CountUp value={s.comissao_base ?? 0} format={fmt.brl} />}
                        hint="Soma do valor de cada rubrica (VALOR_AM) × a quantidade de ações fechadas no período."
                        footer={<FootRow left="Rubricas × ações fechadas" />}
                    />
                    <HeroStat
                        label="Valor FM"
                        icon="trend-up"
                        tone="info"
                        value={<CountUp value={s.fator_multiplicador ?? 0} format={fmt.fator} />}
                        hint="Fator multiplicador do período, pelo valor de causa protocolado (conta a partir de R$ 2,5 mi; trava em 4 ao chegar a R$ 4 mi)."
                        footer={<FootRow left="Fator multiplicador do período" />}
                    />
                    <HeroStat
                        label="Proporcional AM/PA"
                        icon="users"
                        tone="neutral"
                        value={<CountUp value={s.proporcional_am_pa ?? 0} format={fmt.brl} />}
                        hint="Parte da comissão com FM (já sem o desconto) que vai para os estados AM e PA."
                        footer={<FootRow left="Comissão dos estados AM e PA" />}
                    />
                    <HeroStat
                        label="Proporcional PB"
                        icon="users"
                        tone="neutral"
                        value={<CountUp value={s.proporcional_pb ?? 0} format={fmt.brl} />}
                        hint="Parte da comissão com FM (já sem o desconto) que vai para a PB."
                        footer={<FootRow left="Comissão do estado da PB" />}
                    />
                    <HeroStat
                        label="Comissão com FM"
                        icon="check-circle"
                        tone="ok"
                        value={<CountUp value={s.comissao_com_fm_liquida ?? 0} format={fmt.brl} />}
                        hint={`Comissão base × FM, já sem o desconto de cancelamentos tardios (comissionadas antes e canceladas neste período: o valor cheio, sem FM). Bruta, sem o desconto: ${fmt.brl(s.comissao_com_fm ?? 0)}. É o que os proporcionais dividem.`}
                        footer={
                            <FootRow
                                left="Desconto por cancelamento"
                                right={
                                    <strong className={`num${desconto > 0 ? ' tone-text-danger' : ''}`}>
                                        {desconto > 0 ? `− ${fmt.brl(desconto)}` : fmt.brl(0)}
                                    </strong>
                                }
                            />
                        }
                    />
                </div>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Detalhamento"
                title="Protocoladas, rubricas e distribuição"
                subtitle="Valor de causa por atendente, tabela de rubricas e visão consolidada no gráfico."
            >
                <div className="grid comissao-detalhe">
                    <div className="comissao-col">
                        <ChartCard
                            title="Protocoladas · valor de causa"
                            subtitle={`${protocoladas.length} ${protocoladas.length === 1 ? 'atendente' : 'atendentes'} · clique para filtrar`}
                        >
                            <div className="comissao-scroll">
                                <BarList
                                    items={protocoladas}
                                    format={fmt.brl}
                                    ranked
                                    valueOutside
                                    selected={filters.atendente_comercial}
                                    onSelect={porAtendente}
                                    selectLabel="Filtrar pelo atendente"
                                />
                            </div>
                        </ChartCard>
                        <ChartCard
                            title="Valor das rubricas"
                            subtitle={`Mesmo recorte do gráfico de rubricas (${recorte})`}
                        >
                            <div className="at-table-wrap comissao-scroll">
                                <table className="at-table rv-table">
                                    <thead>
                                        <tr>
                                            <th scope="col">
                                                <button
                                                    type="button"
                                                    className="rv-sort"
                                                    onClick={() => setOrdem((o) => proximaOrdem(o, 'rubrica'))}
                                                >
                                                    Rubrica {seta('rubrica')}
                                                </button>
                                            </th>
                                            <th scope="col" className="num">
                                                <button
                                                    type="button"
                                                    className="rv-sort"
                                                    onClick={() => setOrdem((o) => proximaOrdem(o, 'acoes'))}
                                                >
                                                    Ações {seta('acoes')}
                                                </button>
                                            </th>
                                            <th scope="col" className="num">
                                                Valor AM
                                            </th>
                                            <th scope="col" className="num">
                                                Total
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {tabela.linhas.length === 0 ? (
                                            <tr>
                                                <td colSpan={4} className="rv-vazio">
                                                    Não há rubricas para este filtro.
                                                </td>
                                            </tr>
                                        ) : (
                                            tabela.linhas.map((l) => (
                                                <tr key={l.rubrica}>
                                                    <th scope="row" title={l.rubrica}>
                                                        {l.rubrica}
                                                    </th>
                                                    <td className="num">{fmt.int(l.acoes)}</td>
                                                    <td className="num">{brl(l.valorAm)}</td>
                                                    <td className="num strong">{brl(l.total)}</td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                    {tabela.linhas.length > 0 && (
                                        <tfoot>
                                            <tr>
                                                <th scope="row">Total</th>
                                                <td className="num">{fmt.int(tabela.totalAcoes)}</td>
                                                <td className="num muted">—</td>
                                                <td className="num">{fmt.brl(tabela.totalValor)}</td>
                                            </tr>
                                        </tfoot>
                                    )}
                                </table>
                            </div>
                        </ChartCard>
                    </div>
                    <ChartCard
                        className="comissao-pie"
                        title="Rubricas total"
                        subtitle={`${fmt.int(tabela.totalAcoes)} ações fechadas · ${pontos.length} rubricas`}
                        action={
                            <label className="field-select">
                                <span className="sr-only">Origem</span>
                                <select value={canal} onChange={(e) => setCanal(e.target.value)}>
                                    {canais.map((c) => (
                                        <option key={c} value={c}>
                                            {c === 'total' ? 'Total de rubricas' : rotuloCanal(c)}
                                        </option>
                                    ))}
                                </select>
                            </label>
                        }
                    >
                        <PieChart
                            items={pontos}
                            size={260}
                            centerLabel="ações fechadas"
                            labels
                            legendWhenNarrow
                            selected={filters.rubrica}
                            onSelect={porRubrica}
                            selectLabel="Filtrar pela rubrica"
                        />
                    </ChartCard>
                </div>
            </DashSection>
        </div>
    )
}
