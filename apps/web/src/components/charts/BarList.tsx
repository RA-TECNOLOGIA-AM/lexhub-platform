import type { CSSProperties } from 'react'
import type { Point } from '../../types/index.ts'
import { fmt } from '../../lib/format.ts'
import { Icon } from '../ui/Icon.tsx'
import { ChartEmpty } from './ChartCard.tsx'

type BarListProps = {
    items: Point[]
    total?: number // base do % (padrão: a soma das linhas)
    format?: (v: number) => string
    showShare?: boolean // % de cada linha no total (coluna da direita)
    selected?: string[] // linhas do filtro em uso (destacadas)
    onSelect?: (name: string) => void // clicar numa linha filtra o dashboard por ela
    selectLabel?: string // "Filtrar pela matéria" (leitor de tela)
    stacked?: string[] // linhas que são um pacote (rubrica reunida): ganham o ícone de camadas
}

// Módulo: barras horizontais sobre um trilho, com o nome à esquerda e o % à direita (Top 10 por matéria).
// HTML, não SVG: o layout acompanha a largura sozinho.
export function BarList({
    items,
    total,
    format = fmt.int,
    showShare = false,
    selected = [],
    onSelect,
    selectLabel = 'Filtrar por',
    stacked = [],
}: BarListProps) {
    if (items.length === 0) return <ChartEmpty />
    const base = total ?? items.reduce((sum, p) => sum + p.value, 0)
    const top = Math.max(...items.map((p) => p.value)) || 1

    return (
        <ul className={showShare ? 'barlist share' : 'barlist'} role="list">
            {items.map((p) => {
                const pct = (p.value / top) * 100
                const active = selected.includes(p.name)
                const dim = selected.length > 0 && !active
                const label = format(p.value)
                const style = { '--w': `${Math.max(pct, 3)}%` } as CSSProperties
                const content = (
                    <>
                        <span className="barlist-name num" title={p.name}>
                            {stacked.includes(p.name) && (
                                <span className="barlist-stack" title="Rubrica reunida: clique para ver as rubricas">
                                    <Icon name="layers" size={13} />
                                </span>
                            )}
                            {p.name}
                        </span>
                        <span className="barlist-track">
                            <span className="barlist-bar" style={style}>
                                <span className="barlist-v num">{label}</span>
                            </span>
                        </span>
                        {showShare && (
                            <span className="barlist-share num">{base ? Math.round((p.value / base) * 100) : 0}%</span>
                        )}
                    </>
                )
                return (
                    <li key={p.name} className={dim ? 'barlist-row dim' : 'barlist-row'}>
                        {onSelect ? (
                            <button
                                type="button"
                                className="barlist-hit"
                                aria-pressed={active}
                                aria-label={`${stacked.includes(p.name) ? 'Ver as rubricas de' : selectLabel} ${p.name} (${label})`}
                                onClick={() => onSelect(p.name)}
                            >
                                {content}
                            </button>
                        ) : (
                            <div className="barlist-hit">{content}</div>
                        )}
                    </li>
                )
            })}
        </ul>
    )
}
