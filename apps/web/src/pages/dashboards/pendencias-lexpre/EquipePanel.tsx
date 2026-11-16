import type { CSSProperties } from 'react'
import { ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { Pill } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { fmt } from '../../../lib/format.ts'
import type { PendenciasResponse } from '../../../types/index.ts'
import { initials } from '../setor/setor.ts'

type Comissao = PendenciasResponse['comissionamento_pendencias_por_funcionario'][number]

type EquipePanelProps = {
    media: { name: string; value: number }[] // resolvidas por dia, por pessoa (todos veem)
    comissao: Comissao[] // quem gere a unidade recebe de todos; os demais, só a própria linha
    meta: number // meta diária por pessoa
    metaTaxa: number // taxa de resolvido mínima (faixa de comissão da v1)
    maxCancelamento: number // taxa de cancelamento máxima (faixa de comissão da v1)
    filteredTo: string[]
    onFilterPerson?: (name: string) => void
}

// Módulo: "Desempenho por funcionário" de Pendências. A API manda, de todos, só a média diária de cada pessoa;
// resolvidas e taxas vêm na tabela de comissão (quem gere vê de todos). Mesmo visual do painel dos outros setores.
export function EquipePanel({
    media,
    comissao,
    meta,
    metaTaxa,
    maxCancelamento,
    filteredTo,
    onFilterPerson,
}: EquipePanelProps) {
    const pessoas = [...media].sort((a, b) => b.value - a.value || a.name.localeCompare(b.name))
    if (pessoas.length === 0) return <ChartEmpty>Nenhum funcionário resolveu pendências no período.</ChartEmpty>
    const porNome = new Map(comissao.map((c) => [c.funcionario, c]))

    return (
        <div className="fpanel">
            <div className="fpanel-tools">
                <span className="muted small">
                    {pessoas.length} {pessoas.length === 1 ? 'funcionário' : 'funcionários'} · Setor de Pendências
                </span>
                <span className="meta-chip num">
                    Meta: <strong>{fmt.int(meta)}</strong>/dia
                </span>
            </div>
            <ul className="fplist" role="list">
                {pessoas.map((p) => {
                    const c = porNome.get(p.name)
                    const ok = p.value >= meta
                    const scale = Math.max(meta * 1.25, p.value) || 1
                    const active = filteredTo.includes(p.name)
                    const who = (
                        <>
                            <span className="favatar num" aria-hidden="true">
                                {initials(p.name)}
                            </span>
                            <span className="fperson-text">
                                <strong>{p.name}</strong>
                                <span className="muted small num">
                                    {c ? `${fmt.int(c.qtd_resolvido)} resolvidas no período` : 'Setor de Pendências'}
                                </span>
                            </span>
                        </>
                    )
                    return (
                        <li key={p.name} className={active ? 'fpcard on' : 'fpcard'}>
                            <div className="fpcard-head">
                                {onFilterPerson ? (
                                    <button
                                        type="button"
                                        className="fpcard-who"
                                        aria-pressed={active}
                                        title={
                                            active ? 'Tirar o filtro desta pessoa' : 'Filtrar a página por esta pessoa'
                                        }
                                        onClick={() => onFilterPerson(p.name)}
                                    >
                                        {who}
                                    </button>
                                ) : (
                                    <span className="fpcard-who">{who}</span>
                                )}
                                <Pill tone={ok ? 'ok' : 'warn'}>{ok ? 'Na meta' : 'Abaixo da meta'}</Pill>
                            </div>
                            <div className={c ? 'fpcard-metrics three' : 'fpcard-metrics'}>
                                <div className="fstack">
                                    <span className="muted small">Média diária</span>
                                    <span className="fbox-row tight">
                                        <strong className={`num tone-text-${ok ? 'ok' : 'warn'}`}>
                                            <CountUp value={p.value} format={fmt.dec2} />
                                        </strong>
                                        {meta > 0 && (
                                            <span className={`small num tone-text-${ok ? 'ok' : 'warn'}`}>
                                                {ok ? '+' : '-'}
                                                {fmt.dec1(Math.abs(((p.value - meta) / meta) * 100))}%
                                            </span>
                                        )}
                                    </span>
                                    <span className="gauge" aria-hidden="true">
                                        <span
                                            className={`gauge-bar tone-${ok ? 'ok' : 'warn'}`}
                                            style={{ '--w': `${(p.value / scale) * 100}%` } as CSSProperties}
                                        />
                                        <span className="gauge-mark" style={{ left: `${(meta / scale) * 100}%` }} />
                                    </span>
                                </div>
                                {c && (
                                    <>
                                        <div className="fstack">
                                            <span className="muted small">Taxa resolvido</span>
                                            <strong
                                                className={`num tone-text-${c.taxa_resolvido >= metaTaxa ? 'ok' : 'warn'}`}
                                            >
                                                {fmt.dec1(c.taxa_resolvido)}%
                                            </strong>
                                            <span className="small muted num">mín. {fmt.int(metaTaxa)}%</span>
                                        </div>
                                        <div className="fstack">
                                            <span className="muted small">Taxa cancelamento</span>
                                            <strong
                                                className={`num tone-text-${c.taxa_cancelamento < maxCancelamento ? 'ok' : 'danger'}`}
                                            >
                                                {fmt.dec1(c.taxa_cancelamento)}%
                                            </strong>
                                            <span className="small muted num">máx. {fmt.int(maxCancelamento)}%</span>
                                        </div>
                                    </>
                                )}
                            </div>
                        </li>
                    )
                })}
            </ul>
        </div>
    )
}
