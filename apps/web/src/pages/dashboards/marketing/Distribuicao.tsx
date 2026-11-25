import type { CSSProperties } from 'react'
import { ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { fmt } from '../../../lib/format.ts'
import type { Point } from '../../../types/index.ts'
import { ehEmBranco, participacao, totalDe } from './marketingComum.ts'

// Distribuição de uma dimensão (campanha, posicionamento...): nome, barra com o valor dentro e o % à direita.
// "(Em branco)" em itálico e cinza. Clicar numa linha filtra a página.
export function Distribuicao(p: {
    itens: Point[]
    tone: 'accent' | 'ok'
    selected?: string[]
    onSelect?: (name: string) => void
    selectLabel?: string
}) {
    const selected = p.selected ?? []
    const total = totalDe(p.itens)
    const max = Math.max(0, ...p.itens.map((i) => i.value))
    if (max === 0) return <ChartEmpty />
    const isSel = (name: string) => selected.some((s) => s.toUpperCase() === name.toUpperCase())
    return (
        <ul className={`mkt-dist tone-${p.tone}`} role="list">
            {p.itens.map((i) => (
                <li key={i.name}>
                    <button
                        type="button"
                        disabled={!p.onSelect}
                        aria-pressed={p.onSelect ? isSel(i.name) : undefined}
                        aria-label={`${p.selectLabel ?? 'Filtrar por'} ${i.name}`}
                        className={[
                            ehEmBranco(i.name) ? 'branco' : '',
                            selected.length > 0 && !isSel(i.name) ? 'dim' : '',
                        ]
                            .filter(Boolean)
                            .join(' ')}
                        onClick={() => p.onSelect?.(i.name)}
                    >
                        <span className="mkt-dist-nome num" title={i.name}>
                            {i.name}
                        </span>
                        <span className="mkt-dist-trilho">
                            <span style={{ '--w': `${Math.max(7, participacao(i.value, max))}%` } as CSSProperties}>
                                <span className="num">{fmt.int(i.value)}</span>
                            </span>
                        </span>
                        <span className="num muted mkt-dist-pct">{`${Math.round(participacao(i.value, total))}%`}</span>
                    </button>
                </li>
            ))}
        </ul>
    )
}
