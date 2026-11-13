import type { UnitSources } from '../../../types/index.ts'
import { unitLimitLabel, unitSub } from './sourcesView.ts'

type UnitNavProps = {
    units: UnitSources[]
    selected?: string // código da unidade aberta
    limit: { used: number; total: number } | null // null = o plano não limita
    onPick: (code: string) => void
    onAdd: () => void
}

// Módulo: a lista de unidades da página (escolher uma, "+ Nova unidade" e o limite do plano).
// Não sabe de URL nem de dados: recebe tudo por props e avisa o clique pelo onPick.
export function UnitNav({ units, selected, limit, onPick, onAdd }: UnitNavProps) {
    const limitLabel = unitLimitLabel(limit)
    return (
        <nav aria-label="Unidades" className="card unit-nav">
            {units.map((u) => (
                <button
                    key={u.unit.code}
                    type="button"
                    className="unit-btn"
                    aria-current={u.unit.code === selected}
                    onClick={() => onPick(u.unit.code)}
                >
                    <span className="unit-name">{u.unit.name}</span>
                    <span className="unit-sub">{unitSub(u)}</span>
                </button>
            ))}
            <button type="button" className="unit-btn unit-add" onClick={onAdd}>
                + Nova unidade
            </button>
            {limitLabel && <span className="unit-limit">{limitLabel}</span>}
        </nav>
    )
}
