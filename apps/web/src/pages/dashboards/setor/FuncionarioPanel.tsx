import type { CSSProperties } from 'react'
import { ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { Pill } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { fmt } from '../../../lib/format.ts'
import { initials, share, type Funcionario } from './setor.ts'

// Os nomes de cada setor no painel ("Protocolados"/"Represados", "Peticionados"/"Não peticionados"...).
export type PainelLabels = {
    setor: string // "Protocolo"
    feitos: string // "Protocolados"
    pendentes: string // "Represados"
    alerta: string // "não protocolados" (o aviso de fila, em minúsculas)
    media: string // "Média diária"
    valor: string // "Valor protocolado"
    valorSecundario?: string // "Protocolado" (parte do valor já resolvida, quando o setor tem)
    valorRestante?: string // "Falta protocolar" (o resto do valor)
}

type FuncionarioPanelProps = {
    people: Funcionario[]
    unit: string // código da unidade ("LAAM")
    meta: number // meta diária por funcionário
    labels: PainelLabels
    filteredTo: string[] // filtro de funcionário em uso (a pessoa fica destacada)
    onFilterPerson?: (name: string) => void // clicar no nome liga/desliga o filtro dela
}

// Módulo: "Desempenho por funcionário" (comum aos dashboards de setor). Todas as pessoas, uma embaixo da outra:
// demandas (feitas × na fila), média diária contra a meta, valor de causa e o aviso de fila.
// Para ver uma só, o filtro de funcionário (janela Filtros ou clique no nome) recorta a página toda.
export function FuncionarioPanel({ people, unit, meta, labels, filteredTo, onFilterPerson }: FuncionarioPanelProps) {
    if (people.length === 0) return <ChartEmpty>Nenhum funcionário com demanda no período.</ChartEmpty>
    const totalOperacao = people.reduce((sum, f) => sum + f.feitos + f.pendentes, 0)

    return (
        <div className="fpanel">
            <div className="fpanel-tools">
                <span className="muted small">
                    {people.length} {people.length === 1 ? 'funcionário' : 'funcionários'} · Setor de {labels.setor} ·{' '}
                    {unit}
                </span>
                <span className="meta-chip num">
                    Meta: <strong>{fmt.int(meta)}</strong>/dia
                </span>
            </div>
            <ul className="fplist" role="list">
                {people.map((p) => (
                    <PersonCard
                        key={p.name}
                        p={p}
                        meta={meta}
                        labels={labels}
                        pctOperacao={share(p.feitos + p.pendentes, totalOperacao)}
                        active={filteredTo.includes(p.name)}
                        onFilter={onFilterPerson}
                    />
                ))}
            </ul>
        </div>
    )
}

function PersonCard({
    p,
    meta,
    labels,
    pctOperacao,
    active,
    onFilter,
}: {
    p: Funcionario
    meta: number
    labels: PainelLabels
    pctOperacao: number
    active: boolean
    onFilter?: (name: string) => void
}) {
    const demandas = p.feitos + p.pendentes
    const media = p.mediaDiaria ?? 0
    const ok = media >= meta
    const scale = Math.max(meta * 1.25, media) || 1
    // Setor com parte já resolvida do valor (Peticionamento): protocolado × falta protocolar.
    const dividido = !!labels.valorSecundario && !!labels.valorRestante && p.valorSecundario !== null
    const feito = p.valorSecundario ?? 0
    const falta = Math.max(0, p.valorCausa - feito)
    const name = (
        <>
            <span className="favatar num" aria-hidden="true">
                {initials(p.name)}
            </span>
            <span className="fperson-text">
                <strong>{p.name}</strong>
                <span className="muted small num">{fmt.dec1(pctOperacao)}% da operação</span>
            </span>
        </>
    )
    return (
        <li className={active ? 'fpcard on' : 'fpcard'}>
            <div className="fpcard-head">
                {onFilter ? (
                    <button
                        type="button"
                        className="fpcard-who"
                        aria-pressed={active}
                        title={active ? 'Tirar o filtro desta pessoa' : 'Filtrar a página por esta pessoa'}
                        onClick={() => onFilter(p.name)}
                    >
                        {name}
                    </button>
                ) : (
                    <span className="fpcard-who">{name}</span>
                )}
                <Pill tone={p.feitos > 0 ? 'accent' : 'neutral'}>{p.feitos > 0 ? 'Em atividade' : 'Sem produção'}</Pill>
            </div>

            <div className="fbox-row small">
                <span className="muted">Demandas no período</span>
                <strong className="num">
                    <CountUp value={demandas} format={fmt.int} />
                </strong>
            </div>
            <div className="split" aria-hidden="true">
                <span className="split-a" style={{ flexGrow: p.feitos }} />
                <span className="split-b" style={{ flexGrow: p.pendentes }} />
            </div>
            <div className="fbox-row small num">
                <span>
                    <span className="dot tone-accent" /> {labels.feitos}: <strong>{fmt.int(p.feitos)}</strong>
                </span>
                <span>
                    <span className="dot tone-danger" /> {labels.pendentes}: <strong>{fmt.int(p.pendentes)}</strong>
                </span>
            </div>

            <div className={dividido ? 'fpcard-metrics three' : 'fpcard-metrics'}>
                <div className="fstack">
                    <span className="muted small">{labels.media}</span>
                    <span className="fbox-row tight">
                        <strong className={`num tone-text-${ok ? 'ok' : 'warn'}`}>
                            {p.mediaDiaria === null ? '—' : <CountUp value={media} format={fmt.dec2} />}
                        </strong>
                        {p.mediaDiaria !== null && meta > 0 && (
                            <span className={`small num tone-text-${ok ? 'ok' : 'warn'}`}>
                                {ok ? '+' : '-'}
                                {fmt.dec1(Math.abs(((media - meta) / meta) * 100))}%
                            </span>
                        )}
                    </span>
                    <span className="gauge" aria-hidden="true">
                        <span
                            className={`gauge-bar tone-${ok ? 'ok' : 'warn'}`}
                            style={{ '--w': `${(media / scale) * 100}%` } as CSSProperties}
                        />
                        <span className="gauge-mark" style={{ left: `${(meta / scale) * 100}%` }} />
                    </span>
                </div>
                {dividido ? (
                    <>
                        {/* Peticionamento: o valor já protocolado e o que falta protocolar, lado a lado (como na v1). */}
                        <div className="fstack">
                            <span className="muted small">{labels.valorSecundario}</span>
                            <strong className="num tone-text-ok">
                                <CountUp value={feito} format={fmt.brl} />
                            </strong>
                            <span className="small muted num">{fmt.dec1(share(feito, p.valorCausa))}% do total</span>
                        </div>
                        <div className="fstack">
                            <span className="muted small">{labels.valorRestante}</span>
                            <strong className="num tone-text-info">
                                <CountUp value={falta} format={fmt.brl} />
                            </strong>
                            <span className="small muted num">{fmt.dec1(share(falta, p.valorCausa))}% do total</span>
                        </div>
                    </>
                ) : (
                    <div className="fstack">
                        <span className="muted small">{labels.valor}</span>
                        <strong className="num">
                            <CountUp value={p.valorCausa} format={fmt.brl} />
                        </strong>
                    </div>
                )}
            </div>

            {p.pendentes > 0 && (
                <div className="fpcard-alert">
                    <Icon name="alert" size={15} />
                    <span>
                        <strong className="num">{fmt.int(p.pendentes)}</strong> {labels.alerta} na fila
                    </span>
                </div>
            )}
        </li>
    )
}
