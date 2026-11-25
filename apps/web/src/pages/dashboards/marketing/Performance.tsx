import { useState, type ReactNode } from 'react'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { Pill } from '../../../components/dashboard/StatCard.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import { Distribuicao } from './Distribuicao.tsx'
import {
    DIMS_DIST,
    OPCOES_DIST,
    ehEmBranco,
    lider,
    totalDe,
    type DimDist,
    type Dimensao,
    type Leitor,
} from './marketingComum.ts'

const pct1 = (v: number) => `${fmt.dec1(v)}%`

// Card de número com faixa colorida em cima, o valor grande e uma linha de contexto.
export function Numero(p: {
    label: string
    tone: Tone
    value: number
    format: (v: number) => string
    legenda?: ReactNode
    valorNaCor?: boolean
}) {
    return (
        <div className={`card hero tone-${p.tone} mkt-num`}>
            <span className="hero-l">{p.label}</span>
            <span className={`mkt-num-v num${p.valorNaCor ? ' tone-text' : ''}`}>
                <CountUp value={p.value} format={p.format} />
            </span>
            {p.legenda && <span className="mkt-num-legenda">{p.legenda}</span>}
        </div>
    )
}

// Os campos da campanha de cada página: no banco NG, a campanha NG (ANUNCIO_NG); no LexPre, a campanha (anúncio).
export type CamposPerformance = {
    sufixo: string // ' NG' | ''
    codigo?: string // 'ANUNCIO_NG' (no subtítulo)
    leads: string
    clientes: string
    acoes: string
    conversao: string
    cpl: string
    valorCausa: string
    ticket: string
    rubricas: string // o gráfico de rubricas da campanha
}

type PerformanceProps = {
    ler: Leitor
    index: number
    campos: CamposPerformance
    filters: DashboardFilters
    onToggleFilter?: (key: Dimensao, value: string) => void
}

// 06 · Indicadores de performance da campanha: o caminho gasto -> leads -> clientes -> ações, os custos e o retorno,
// as rubricas e a distribuição por campanha/posicionamento/conjunto/criativo/categoria.
export function Performance({ ler, index, campos: c, filters, onToggleFilter }: PerformanceProps) {
    const { n, serie } = ler
    const [dim, setDim] = useState<DimDist>('campanha')
    const gasto = n('facebook_valor_gasto')
    const leads = n(c.leads)
    const clientes = n(c.clientes)
    const acoes = n(c.acoes)
    const itens = serie(`ind_${dim}`)
    const criativo = lider(serie('ind_criativo').filter((p) => !ehEmBranco(p.name)))
    const rubricas = serie(c.rubricas)
    const clique = (d: Dimensao, rotulo: string) => ({
        selected: filters[d] ?? [],
        onSelect: onToggleFilter && ((name: string) => onToggleFilter(d, name)),
        selectLabel: `Filtrar por ${rotulo.toLowerCase()}`,
    })
    const passos: { label: string; value: ReactNode; extra?: ReactNode }[] = [
        { label: '1. Valor gasto', value: <span className="tone-text-danger">{fmt.brl(gasto)}</span> },
        { label: `2. Leads${c.sufixo}`, value: <span className="tone-text-info">{fmt.int(leads)}</span> },
        {
            label: `3. Clientes${c.sufixo}`,
            value: fmt.int(clientes),
            extra: <span className="tone-text-ok">({pct1(n(c.conversao))} conv.)</span>,
        },
        {
            label: `4. Ações${c.sufixo}`,
            value: <span className="tone-text-accent">{fmt.int(acoes)}</span>,
            extra: `(${fmt.dec2(clientes > 0 ? acoes / clientes : 0)} ações/cliente)`,
        },
    ]

    return (
        <DashSection
            index={index}
            eyebrow={`Ind. Performance de MKT${c.sufixo ? ` —${c.sufixo}` : ''}`}
            title={`Indicadores de performance${c.sufixo ? ` —${c.sufixo}` : ''}`}
            subtitle={
                c.codigo
                    ? `Indicadores consolidados da campanha ${c.codigo}.`
                    : 'Indicadores consolidados da campanha (anúncio).'
            }
        >
            <div className="card mkt-passos">
                {passos.map((p, i) => (
                    <div key={p.label} className="mkt-passo">
                        <span className="mkt-passo-txt">
                            <span className="hero-l">{p.label}</span>
                            <span className="mkt-passo-v num">
                                {p.value} {p.extra && <span className="mkt-passo-extra">{p.extra}</span>}
                            </span>
                        </span>
                        {i < passos.length - 1 && <Icon name="arrowRight" size={14} />}
                    </div>
                ))}
            </div>

            <div className="mkt-grid-4 grid-mini">
                <Numero
                    label="CPL (custo por lead)"
                    tone="info"
                    value={n(c.cpl)}
                    format={fmt.brl}
                    legenda={<span className="tone-text-info">{`${fmt.int(leads)} leads gerados`}</span>}
                />
                <Numero
                    label="CAC (custo por cliente)"
                    tone="accent"
                    value={n('facebook_cac_campanha')}
                    format={fmt.brl}
                    legenda={<span className="tone-text-accent">{`${fmt.int(clientes)} clientes fechados`}</span>}
                />
                <Numero
                    label="ROAS"
                    tone="ok"
                    value={n('facebook_roas_campanha')}
                    format={(v) => `${fmt.dec2(v)}x`}
                    legenda="Retorno sobre valor de causa"
                    valorNaCor
                />
                <Numero
                    label="Valor de causa protocolado"
                    tone="ok"
                    value={n(c.valorCausa)}
                    format={fmt.brl}
                    legenda={
                        <span className="tone-text-ok">
                            Ticket médio: <strong className="num">{fmt.brl(n(c.ticket))}</strong>
                        </span>
                    }
                />
            </div>

            <div className="mkt-grid-lado grid-mini">
                <ChartCard
                    title={`Rubricas (ações${c.sufixo})`}
                    subtitle="Todas as rubricas, cada uma com a sua fatia. Clique numa fatia para filtrar"
                    action={rubricas.length > 0 && <Pill tone="accent">{`${fmt.int(totalDe(rubricas))} ações`}</Pill>}
                >
                    <PieChart
                        items={rubricas}
                        size={240}
                        labels
                        legendWhenNarrow
                        centerLabel="ações"
                        {...clique('rubrica_marketing', 'rubrica')}
                    />
                </ChartCard>
                <ChartCard
                    title={`Distribuição por ${DIMS_DIST[dim].label.toLowerCase()}`}
                    subtitle={`Concentração de leads e atribuição UTM na campanha${c.sufixo}`}
                    action={<Segmented label="Dimensão" options={OPCOES_DIST} value={dim} onChange={setDim} />}
                    footer={
                        <div className="mkt-dist-rodape">
                            <span>
                                Criativo líder:{' '}
                                {criativo ? (
                                    <strong className="num tone-text-accent">
                                        {criativo.name} ({Math.round(criativo.share)}%)
                                    </strong>
                                ) : (
                                    '—'
                                )}
                            </span>
                            <span className="num">Base: {fmt.int(totalDe(itens))} leads</span>
                        </div>
                    }
                >
                    <Distribuicao itens={itens} tone="accent" {...clique(DIMS_DIST[dim].dim, DIMS_DIST[dim].label)} />
                </ChartCard>
            </div>
        </DashSection>
    )
}
