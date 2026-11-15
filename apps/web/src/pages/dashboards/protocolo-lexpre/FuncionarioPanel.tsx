import { useState, type CSSProperties } from 'react'
import { ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { Pill, ToneIcon } from '../../../components/dashboard/StatCard.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { fmt } from '../../../lib/format.ts'
import { initials, share, type Funcionario } from './charts.ts'

type FuncionarioPanelProps = {
    people: Funcionario[]
    unit: string // código da unidade ("LAAM")
    meta: number // meta diária de protocolos por funcionário
    // Matéria dos represados (a primeira de represados_por_materia). Só vale para a pessoa quando a lista
    // já está recortada nela (uma pessoa só ou filtro de funcionário em uso).
    represadoMateria: string | null
    filteredTo: string[] // filtro de funcionário em uso
    onFilterPerson?: (name: string) => void
    onFilterMateria?: (materia: string) => void
}

// Módulo: "Desempenho por funcionário". Uma pessoa por vez (seletor quando há mais de uma): demandas,
// média diária contra a meta, valor de causa e o aviso de não protocolados.
export function FuncionarioPanel({
    people,
    unit,
    meta,
    represadoMateria,
    filteredTo,
    onFilterPerson,
    onFilterMateria,
}: FuncionarioPanelProps) {
    const [chosen, setChosen] = useState<string | null>(null)
    if (people.length === 0) return <ChartEmpty>Nenhum funcionário com demanda no período.</ChartEmpty>

    const preferred = chosen ?? (filteredTo.length === 1 ? filteredTo[0] : null)
    const p = people.find((f) => f.name === preferred) ?? people[0]
    const totalOperacao = people.reduce((sum, f) => sum + f.protocolados + f.represados, 0)
    const demandas = p.protocolados + p.represados
    const isolated = people.length === 1 || (filteredTo.length === 1 && filteredTo[0] === p.name)
    const materia = isolated ? represadoMateria : null

    return (
        <div className="fpanel">
            <div className="fpanel-tools">
                {people.length > 1 && (
                    <label className="fpanel-select">
                        <span className="sr-only">Funcionário</span>
                        <select value={p.name} onChange={(e) => setChosen(e.target.value)}>
                            {people.map((f) => (
                                <option key={f.name} value={f.name}>
                                    {f.name} ({fmt.int(f.protocolados + f.represados)})
                                </option>
                            ))}
                        </select>
                    </label>
                )}
                <Pill tone="ok">
                    {fmt.int(Math.round(share(demandas, totalOperacao)))}% da operação {unit}
                </Pill>
            </div>

            <div className="fbox fperson">
                <span className="favatar num" aria-hidden="true">
                    {initials(p.name)}
                </span>
                <span className="fperson-text">
                    <strong>{p.name}</strong>
                    <span className="muted small">Setor de Protocolo · {unit}</span>
                </span>
                <Pill tone={p.protocolados > 0 ? 'accent' : 'neutral'}>
                    {p.protocolados > 0 ? 'Em atividade' : 'Sem produção'}
                </Pill>
            </div>

            <div className="fbox">
                <div className="fbox-row">
                    <span className="muted">Demandas totais no período</span>
                    <strong className="num fbig">{fmt.int(demandas)}</strong>
                </div>
                <div className="split" aria-hidden="true">
                    <span className="split-a" style={{ flexGrow: p.protocolados }} />
                    <span className="split-b" style={{ flexGrow: p.represados }} />
                </div>
                <div className="fbox-row small num">
                    <span>
                        <span className="dot tone-accent" /> Protocolados: <strong>{fmt.int(p.protocolados)}</strong>
                    </span>
                    <span>
                        <span className="dot tone-danger" /> Represados: <strong>{fmt.int(p.represados)}</strong>
                    </span>
                </div>
            </div>

            <MediaDiaria value={p.mediaDiaria} meta={meta} />

            <div className="fbox fbox-row">
                <span className="fstack">
                    <span className="muted small">Valor de causa protocolado</span>
                    <strong className="num fbig">{fmt.brl(p.valorCausa)}</strong>
                </span>
                <ToneIcon icon="dollar" tone="info" />
            </div>

            {p.represados > 0 ? (
                <div className="falert tone-warn">
                    <Icon name="alert" size={18} />
                    <span className="fstack">
                        <strong>
                            Não protocolados: {fmt.int(p.represados)} {p.represados === 1 ? 'caso' : 'casos'}
                        </strong>
                        {materia && <span className="num small">Matéria: {materia}</span>}
                    </span>
                    {(materia ? onFilterMateria : onFilterPerson) && (
                        <button
                            type="button"
                            className="btn btn-sm"
                            onClick={() => (materia ? onFilterMateria?.(materia) : onFilterPerson?.(p.name))}
                        >
                            Inspecionar
                        </button>
                    )}
                </div>
            ) : (
                <div className="falert tone-ok">
                    <Icon name="check-circle" size={18} />
                    <strong>Nenhuma demanda represada</strong>
                </div>
            )}
        </div>
    )
}

// Média diária contra a meta: barra de 0 até 125% da meta (ou do valor, se passar), com a marca da meta.
function MediaDiaria({ value, meta }: { value: number | null; meta: number }) {
    const media = value ?? 0
    const scale = Math.max(meta * 1.25, media) || 1
    const diff = meta > 0 ? ((media - meta) / meta) * 100 : 0
    const ok = media >= meta
    return (
        <div className="fbox">
            <div className="fbox-row">
                <span className="muted">Média diária de protocolos</span>
                <span className="fbox-row tight">
                    <strong className={`num fbig tone-text-${ok ? 'ok' : 'warn'}`}>
                        {value === null ? '—' : fmt.dec2(media)}
                    </strong>
                    <span className="meta-chip num">
                        Meta: <strong>{fmt.int(meta)}</strong>
                    </span>
                </span>
            </div>
            <div className="gauge" aria-hidden="true">
                <span
                    className={`gauge-bar tone-${ok ? 'ok' : 'warn'}`}
                    style={{ '--w': `${(media / scale) * 100}%` } as CSSProperties}
                />
                <span className="gauge-mark" style={{ left: `${(meta / scale) * 100}%` }} />
            </div>
            <div className="fbox-row small num">
                <span className="muted">0/dia</span>
                {value !== null && (
                    <span className={`tone-text-${ok ? 'ok' : 'warn'}`}>
                        {diff >= 0 ? '+' : '-'}
                        {fmt.dec1(Math.abs(diff))}% {ok ? 'acima' : 'abaixo'} da meta
                    </span>
                )}
                <span className="muted">{fmt.int(Math.round(scale))}/dia</span>
            </div>
        </div>
    )
}
