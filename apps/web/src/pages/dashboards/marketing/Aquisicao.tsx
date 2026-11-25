import { useState, type CSSProperties } from 'react'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { Pill, ToneIcon } from '../../../components/dashboard/StatCard.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters, Point } from '../../../types/index.ts'
import { RoscaLegenda } from './RoscaLegenda.tsx'
import { ehEmBranco, lider, participacao, semUtm, totalDe, type Dimensao, type Leitor } from './marketingComum.ts'

const pct1 = (v: number) => `${fmt.dec1(v)}%`
// % curto dos rankings: 58% · 0,4%
const pctCurto = (v: number) => (v >= 1 || v === 0 ? `${Math.round(v)}%` : `${fmt.dec1(v)}%`)

const DIMS = {
    posicionamento: { label: 'Posicionamento', dim: 'posicionamento_marketing' },
    canal_aquisicao: { label: 'Canal de Aquisição', dim: 'canal_aquisicao_marketing' },
    campanha: { label: 'Campanha', dim: 'campanha_marketing' },
} as const satisfies Record<string, { label: string; dim: Dimensao }>
type Dim = keyof typeof DIMS

// Ranking de um lado do comparativo: nome, barra (sobre o maior) e "valor (%)". "(Em branco)" em itálico.
function Ranking(p: {
    titulo: string
    tone: 'accent' | 'ok'
    itens: Point[]
    total: number
    selected: string[]
    onSelect?: (name: string) => void
    selectLabel: string
}) {
    const max = Math.max(0, ...p.itens.map((i) => i.value))
    const isSel = (name: string) => p.selected.some((s) => s.toUpperCase() === name.toUpperCase())
    return (
        <div className={`mkt-rank tone-${p.tone}`}>
            <div className="mkt-rank-head">
                <strong className="tone-text">{p.titulo}</strong>
                <span className="num muted small">Base: {fmt.int(p.total)}</span>
            </div>
            {p.itens.length === 0 ? (
                <p className="chart-empty muted small">Sem dados no período.</p>
            ) : (
                <ul className="mkt-rank-lista" role="list">
                    {p.itens.map((i) => (
                        <li key={i.name}>
                            <button
                                type="button"
                                disabled={!p.onSelect}
                                aria-pressed={p.onSelect ? isSel(i.name) : undefined}
                                aria-label={`${p.selectLabel} ${i.name}`}
                                className={[
                                    ehEmBranco(i.name) ? 'branco' : '',
                                    p.selected.length > 0 && !isSel(i.name) ? 'dim' : '',
                                ]
                                    .filter(Boolean)
                                    .join(' ')}
                                onClick={() => p.onSelect?.(i.name)}
                            >
                                <span className="mkt-rank-nome" title={i.name}>
                                    {i.name}
                                </span>
                                <span className="mkt-trilho">
                                    <span
                                        style={
                                            { '--w': `${Math.max(3, participacao(i.value, max))}%` } as CSSProperties
                                        }
                                    />
                                </span>
                                <span className="num mkt-rank-v">
                                    <strong>{fmt.int(i.value)}</strong>{' '}
                                    <span className="muted">({pctCurto(participacao(i.value, p.total))})</span>
                                </span>
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}

type AquisicaoProps = {
    ler: Leitor
    index: number
    filters: DashboardFilters
    onToggleFilter?: (key: Dimensao, value: string) => void
}

// 05 · Análise de aquisição: o alerta de UTM em branco, as roscas por criativo (trackeamento e fechamento) e o
// comparativo trackeamento x fechamento por dimensão.
export function Aquisicao({ ler, index, filters, onToggleFilter }: AquisicaoProps) {
    const { n, serie } = ler
    const [dim, setDim] = useState<Dim>('posicionamento')
    const [esconderBranco, setEsconderBranco] = useState(false)
    const rastreados = n('total_trackeamento')
    const assinados = n('processos_assinados')
    const utmTrack = semUtm(serie('trackeamento_categoria'))
    const utmFech = semUtm(serie('fechamento_categoria'))
    const lidera = lider(serie('trackeamento_categoria').filter((p) => !ehEmBranco(p.name)))
    const clique = (d: Dimensao) => ({
        selected: filters[d] ?? [],
        onSelect: onToggleFilter && ((name: string) => onToggleFilter(d, name)),
    })
    const lado = (serieKey: string) => {
        const pts = serie(serieKey)
        return { total: totalDe(pts), itens: esconderBranco ? pts.filter((p) => !ehEmBranco(p.name)) : pts }
    }
    const track = lado(`trackeamento_${dim}`)
    const fech = lado(`fechamento_${dim}`)
    const { label, dim: filtro } = DIMS[dim]

    return (
        <DashSection
            index={index}
            eyebrow="Análise de Aquisição"
            title="Análise de aquisição"
            subtitle={`${fmt.int(rastreados)} atendimento(s) rastreado(s) e ${fmt.int(assinados)} processo(s) assinado(s) no período (taxa de conversão: ${pct1(participacao(assinados, rastreados))}).`}
        >
            {(utmTrack.value > 0 || utmFech.value > 0) && (
                <div className="card mkt-alerta" role="note">
                    <ToneIcon icon="alert" tone="warn" />
                    <div className="mkt-alerta-txt">
                        <span className="mkt-alerta-t">
                            <strong>Alerta de Higiene de UTM (Trackeamento → Fechamento)</strong>
                            <Pill tone="warn">{`${pct1(utmFech.share)} sem UTM no fechamento`}</Pill>
                        </span>
                        <span className="muted small">
                            No trackeamento, <strong className="num">{pct1(utmTrack.share)}</strong> chegam sem UTM (
                            <strong className="num tone-text-accent">(Em branco)</strong>); no fechamento esse índice{' '}
                            {utmFech.share >= utmTrack.share ? 'sobe' : 'fica'} para{' '}
                            <strong className="num tone-text-accent">{pct1(utmFech.share)}</strong> (
                            {fmt.int(utmFech.value)} de {fmt.int(utmFech.total)}).
                        </span>
                    </div>
                    <button
                        type="button"
                        className="btn mkt-btn mkt-alerta-btn"
                        aria-pressed={esconderBranco}
                        onClick={() => setEsconderBranco((e) => !e)}
                    >
                        {esconderBranco ? 'Mostrar "(Em branco)" nos rankings' : 'Ocultar "(Em branco)" nos rankings'}
                    </button>
                </div>
            )}

            <div className="mkt-grid-2 grid-mini">
                <ChartCard
                    title="Total trackeamento · Criativo"
                    subtitle="Por categoria do criativo (atendimentos rastreados)"
                    action={lidera && <Pill tone="accent">{`${lidera.name} lidera (${pct1(lidera.share)})`}</Pill>}
                >
                    <RoscaLegenda
                        items={serie('trackeamento_categoria')}
                        centerLabel="rastreados"
                        selectLabel="Filtrar pela categoria"
                        {...clique('categoria_marketing')}
                    />
                </ChartCard>
                <ChartCard
                    title="Total fechamento · Criativo"
                    subtitle="Por categoria do criativo (processos assinados)"
                    action={<Pill tone="ok">{`${fmt.int(assinados)} assinados`}</Pill>}
                >
                    <RoscaLegenda
                        items={serie('fechamento_categoria')}
                        centerLabel="assinados"
                        selectLabel="Filtrar pela categoria"
                        {...clique('categoria_marketing')}
                    />
                </ChartCard>
            </div>

            <div className="grid-mini">
                <ChartCard
                    title="Comparativo trackeamento × fechamento por dimensão"
                    subtitle="Compare a origem dos atendimentos rastreados à esquerda com os contratos assinados à direita"
                    action={
                        <Segmented
                            label="Dimensão"
                            options={(Object.keys(DIMS) as Dim[]).map((d) => ({ value: d, label: DIMS[d].label }))}
                            value={dim}
                            onChange={setDim}
                        />
                    }
                >
                    <div className="mkt-grid-2">
                        <Ranking
                            titulo={`${label} — Trackeamento`}
                            tone="accent"
                            {...track}
                            {...clique(filtro)}
                            selectLabel={`Filtrar por ${label.toLowerCase()}`}
                        />
                        <Ranking
                            titulo={`${label} — Fechamento`}
                            tone="ok"
                            {...fech}
                            {...clique(filtro)}
                            selectLabel={`Filtrar por ${label.toLowerCase()}`}
                        />
                    </div>
                </ChartCard>
            </div>
        </DashSection>
    )
}
