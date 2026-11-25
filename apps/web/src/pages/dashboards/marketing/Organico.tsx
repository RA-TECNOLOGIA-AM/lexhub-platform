import { useState } from 'react'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import { Distribuicao } from './Distribuicao.tsx'
import { Numero } from './Performance.tsx'
import {
    CANAIS_ORGANICO,
    DIMS_DIST,
    OPCOES_DIST,
    ROTULO_CANAL,
    ehEmBranco,
    lider,
    participacao,
    totalDe,
    type CanalOrganico,
    type DimDist,
    type Dimensao,
    type Leitor,
} from './marketingComum.ts'

const pct1 = (v: number) => `${fmt.dec1(v)}%`

// Cor do número de cada canal (a mesma família da paleta dos gráficos).
const COR_CANAL: Record<Exclude<CanalOrganico, 'total'>, string> = {
    instagram: 'var(--accent)',
    site: 'var(--c-info)',
    facebook: 'var(--pie-4)',
    google: 'var(--pie-6)',
}

type OrganicoProps = {
    ler: Leitor
    index: number
    sufixo: string // ' NG' | ''
    filters: DashboardFilters
    onToggleFilter?: (key: Dimensao, value: string) => void
}

// 07 · Indicadores orgânicos: leads por canal (clicar num canal mostra as rubricas dele), os resultados dos canais
// orgânicos, as rubricas e o rastreamento UTM por campanha/posicionamento/conjunto/criativo/categoria.
export function Organico({ ler, index, sufixo, filters, onToggleFilter }: OrganicoProps) {
    const { n, serie } = ler
    const [canal, setCanal] = useState<CanalOrganico>('total')
    const [dim, setDim] = useState<DimDist>('campanha')
    const total = n('org_total_leads')
    const canais = (CANAIS_ORGANICO.filter((c) => c !== 'total') as Exclude<CanalOrganico, 'total'>[])
        .map((c) => ({ c, value: n(`org_leads_${c}`) }))
        .sort((a, b) => b.value - a.value)
    const itens = serie(`org_${dim}`)
    const origem = lider(serie('org_posicionamento').filter((p) => !ehEmBranco(p.name)))
    const clique = (d: Dimensao, rotulo: string) => ({
        selected: filters[d] ?? [],
        onSelect: onToggleFilter && ((name: string) => onToggleFilter(d, name)),
        selectLabel: `Filtrar por ${rotulo.toLowerCase()}`,
    })
    const escolher = (c: CanalOrganico) => setCanal((atual) => (atual === c && c !== 'total' ? 'total' : c))

    return (
        <DashSection
            index={index}
            eyebrow={`Ind. Orgânico de MKT${sufixo ? ` —${sufixo}` : ''}`}
            title={`Indicadores orgânicos${sufixo ? ` —${sufixo}` : ''}`}
            subtitle="Canais orgânicos (Instagram, Site, Facebook e Google). Clique num canal para ver as rubricas dele."
        >
            <div className="mkt-grid-5">
                <button
                    type="button"
                    className={`card mkt-canal mkt-canal-total${canal === 'total' ? ' on' : ''}`}
                    aria-pressed={canal === 'total'}
                    onClick={() => escolher('total')}
                >
                    <span className="hero-l">Total leads orgânicos</span>
                    <span className="mkt-num-v num">
                        <CountUp value={total} format={fmt.int} />
                    </span>
                    <span className="mkt-num-legenda">100% dos canais</span>
                </button>
                {canais.map(({ c, value }) => (
                    <button
                        key={c}
                        type="button"
                        className={`card mkt-canal${canal === c ? ' on' : ''}`}
                        aria-pressed={canal === c}
                        aria-label={`Ver as rubricas de ${ROTULO_CANAL[c]}`}
                        onClick={() => escolher(c)}
                    >
                        <span className="hero-l">{ROTULO_CANAL[c]}</span>
                        <span className="mkt-num-v num" style={{ color: COR_CANAL[c] }}>
                            <CountUp value={value} format={fmt.int} />
                        </span>
                        <span className="mkt-num-legenda">{`${pct1(participacao(value, total))} dos leads`}</span>
                    </button>
                ))}
            </div>

            <div className="mkt-grid-5 grid-mini">
                <Numero label="Contratos" tone="neutral" value={n('org_contratos')} format={fmt.int} />
                <Numero label="Ações" tone="accent" value={n('org_acoes')} format={fmt.int} valorNaCor />
                <Numero
                    label="Aproveitamento"
                    tone="neutral"
                    value={n('org_aproveitamento')}
                    format={fmt.dec2}
                    legenda="ações / contrato"
                />
                <Numero
                    label="Taxa de fechamento"
                    tone="ok"
                    value={n('org_taxa_fechamento')}
                    format={fmt.pct}
                    valorNaCor
                />
                <Numero
                    label="Valor protocolado"
                    tone="neutral"
                    value={n('org_valor_causa')}
                    format={fmt.brl}
                    legenda={
                        <>
                            Ticket: <strong className="num">{fmt.brl(n('org_ticket_medio'))}</strong>
                        </>
                    }
                />
            </div>

            <div className="mkt-grid-lado grid-mini">
                <ChartCard
                    title="Rubricas orgânicas"
                    subtitle="Ações fechadas pelos canais orgânicos, por rubrica. Clique numa fatia para filtrar"
                    action={
                        <Segmented
                            label="Canal"
                            options={CANAIS_ORGANICO.map((c) => ({ value: c, label: ROTULO_CANAL[c] }))}
                            value={canal}
                            onChange={setCanal}
                        />
                    }
                >
                    <PieChart
                        items={serie(`org_rubricas_${canal}`)}
                        size={240}
                        labels
                        legendWhenNarrow
                        centerLabel="ações"
                        {...clique('rubrica_marketing', 'rubrica')}
                    />
                </ChartCard>
                <ChartCard
                    title={`Rastreamento orgânico · ${DIMS_DIST[dim].label}`}
                    subtitle={`Parâmetros UTM capturados na origem orgânica (${fmt.int(totalDe(itens))} eventos)`}
                    action={<Segmented label="Dimensão" options={OPCOES_DIST} value={dim} onChange={setDim} />}
                    footer={
                        <div className="mkt-dist-rodape">
                            <span>
                                Origem principal identificada:{' '}
                                {origem ? (
                                    <strong className="num tone-text-ok">
                                        {origem.name} ({Math.round(origem.share)}%)
                                    </strong>
                                ) : (
                                    '—'
                                )}
                            </span>
                            <span className="num">Base: {fmt.int(totalDe(itens))} registros</span>
                        </div>
                    }
                >
                    <Distribuicao itens={itens} tone="ok" {...clique(DIMS_DIST[dim].dim, DIMS_DIST[dim].label)} />
                </ChartCard>
            </div>
        </DashSection>
    )
}
