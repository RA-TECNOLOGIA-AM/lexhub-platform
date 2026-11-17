import { ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { fmt } from '../../../lib/format.ts'
import { CATEGORIAS } from './julgados.ts'
import type { LinhaRelator } from './types.ts'

// Selo da taxa de procedência do relator, nas faixas da v1 (RecursalRankingMagistradoPanel): 60% ou mais
// verde, 45% ou mais âmbar, abaixo disso vermelho.
const tomTaxa = (taxa: number) => (taxa >= 60 ? 'ok' : taxa >= 45 ? 'warn' : 'danger')

// A taxa como a v1 escreve: até uma casa ('50%', '66,7%').
const nfAte1 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 })
const pctAte1 = (v: number) => nfAte1.format(v)

// Módulo: o "Ranking de Relatores" da v1: cada relator com os acórdãos do período, a taxa de procedência e a
// barra Procedentes / Improcedentes / Extintos. Clicar num relator liga o filtro dele (selected = em uso).
export function RelatoresRanking({
    rows,
    selected = [],
    onSelect,
}: {
    rows: LinhaRelator[]
    selected?: string[]
    onSelect?: (name: string) => void
}) {
    if (rows.length === 0) return <ChartEmpty>Nenhum registro no período selecionado.</ChartEmpty>
    const escolhido = (name: string) => selected.some((s) => s.trim().toLowerCase() === name.trim().toLowerCase())
    const partes = (r: LinhaRelator) => [r.pctProcedentes, r.pctImprocedentes, r.pctExtintos]

    return (
        <div className="jl-rank">
            <ul className="jl-rank-list" role="list">
                {rows.map((r) => {
                    const ativo = escolhido(r.name)
                    const body = (
                        <>
                            <span className="jl-av" aria-hidden="true">
                                {r.initials || r.name.slice(0, 2).toUpperCase()}
                            </span>
                            <span className="jl-rank-main">
                                <span className="jl-rank-top">
                                    <strong className="jl-rank-name" title={r.name}>
                                        {r.name}
                                    </strong>
                                    <span className="jl-rank-casos num">{fmt.int(r.total)} casos</span>
                                    <span className={`jl-taxa-badge num tone-${tomTaxa(r.taxa)}`}>
                                        {pctAte1(r.taxa)}%
                                    </span>
                                </span>
                                <span className="jl-bar" aria-hidden="true">
                                    {partes(r).map((pct, k) =>
                                        pct > 0 ? (
                                            <span
                                                key={CATEGORIAS[k].value}
                                                style={{ width: `${pct}%`, background: CATEGORIAS[k].color }}
                                            />
                                        ) : null,
                                    )}
                                </span>
                            </span>
                        </>
                    )
                    const resumo = `${r.name}: ${fmt.int(r.total)} acórdãos, ${fmt.dec1(r.taxa)}% procedentes (${fmt.int(r.procedentes)} procedentes, ${fmt.int(r.improcedentes)} improcedentes, ${fmt.int(r.extintos)} extintos)`
                    return (
                        <li key={r.name} className={selected.length > 0 && !ativo ? 'dim' : undefined}>
                            {onSelect ? (
                                <button
                                    type="button"
                                    className={ativo ? 'jl-rank-row on' : 'jl-rank-row'}
                                    aria-pressed={ativo}
                                    aria-label={`Filtrar pelo relator ${resumo}`}
                                    onClick={() => onSelect(r.name)}
                                >
                                    {body}
                                </button>
                            ) : (
                                <div className="jl-rank-row" aria-label={resumo}>
                                    {body}
                                </div>
                            )}
                        </li>
                    )
                })}
            </ul>
        </div>
    )
}

// Legenda das três partes da barra (vai no cabeçalho do cartão).
export function LegendaCategorias() {
    return (
        <span className="jl-legend-mini" aria-hidden="true">
            {CATEGORIAS.map((c) => (
                <span key={c.value}>
                    <span className="chart-key" style={{ background: c.color }} />
                    {c.label}
                </span>
            ))}
        </span>
    )
}
