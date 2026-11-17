import { CountUp } from '../../../components/ui/CountUp.tsx'
import { fmt } from '../../../lib/format.ts'
import { CATEGORIAS, type Composicao } from './julgados.ts'

// Módulo: o card "Taxa de procedência (2G)" da v1: % de procedentes entre os acórdãos decididos no período
// (procedentes + improcedentes + extintos) e a barra com as três partes. Os não classificados ficam de fora da
// conta e aparecem só na linha de baixo.
export function TaxaProcedencia({ c, className }: { c: Composicao; className?: string }) {
    return (
        <div className={className ? `card jl-taxa ${className}` : 'card jl-taxa'}>
            <div className="jl-taxa-top">
                <div className="jl-taxa-text">
                    <span className="hero-l">Taxa de procedência (2G) — acórdãos no período</span>
                    <span className="jl-taxa-linha">
                        <span className="jl-taxa-v num">
                            {c.temDados ? <CountUp value={c.taxa} format={(v) => `${fmt.dec1(v)}%`} /> : '–'}
                        </span>
                        <span className="muted small num">
                            {fmt.int(c.procedentes)} procedente(s) de {fmt.int(c.decididos)} decidido(s)
                        </span>
                    </span>
                    <span className="muted small num">
                        {fmt.int(c.total)} acórdão(s) no período
                        {c.naoClassificados > 0 ? ` · ${fmt.int(c.naoClassificados)} não classificado(s)` : ''}
                    </span>
                </div>
                <span className={c.temDados ? 'badge neutral jl-taxa-badge-2g' : 'badge neutral muted'}>
                    {c.temDados ? '2G' : 'Sem dados'}
                </span>
            </div>
            <span className="jl-bar jl-bar-lg" aria-hidden="true">
                {CATEGORIAS.map((k) =>
                    c.pct[k.value] > 0 ? (
                        <span key={k.value} style={{ width: `${c.pct[k.value]}%`, background: k.color }} />
                    ) : null,
                )}
            </span>
            <ul className="jl-taxa-legenda" role="list">
                {CATEGORIAS.map((k) => (
                    <li key={k.value}>
                        <span className="chart-key dot" style={{ background: k.color }} />
                        {k.label} — <span className="num">{fmt.dec1(c.pct[k.value])}%</span>
                    </li>
                ))}
            </ul>
        </div>
    )
}
