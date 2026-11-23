import { useState } from 'react'
import type { DeletedUnit, UnitSources } from '../../../types/index.ts'
import { deletedSub, unitLimitLabel, unitSub } from './sourcesView.ts'

type UnitNavProps = {
    units: UnitSources[]
    selected?: string // código da unidade aberta
    limit: { used: number; total: number } | null // null = o plano não limita
    onPick: (code: string) => void
    onAdd?: () => void // sem onAdd (quem não cria unidade), o "+ Nova unidade" não aparece
    deleted?: DeletedUnit[] // excluídas que ainda dá para restaurar (só quem gere unidades recebe)
    onRestore?: (code: string) => Promise<void> // se rejeitar, quem chama mostra o erro
}

// Módulo: a lista de unidades da página (escolher uma, "+ Nova unidade", o limite do plano e as excluídas
// com "Restaurar"). Não sabe de URL nem de dados: recebe tudo por props e avisa pelo onPick/onRestore.
export function UnitNav({ units, selected, limit, onPick, onAdd, deleted = [], onRestore }: UnitNavProps) {
    const limitLabel = unitLimitLabel(limit)
    const [restoring, setRestoring] = useState<string | null>(null) // código sendo restaurado

    async function restore(code: string) {
        if (!onRestore) return
        setRestoring(code)
        try {
            await onRestore(code)
        } finally {
            setRestoring(null)
        }
    }

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
            {onAdd && (
                <button type="button" className="unit-btn unit-add" onClick={onAdd}>
                    + Nova unidade
                </button>
            )}
            {limitLabel && <span className="unit-limit">{limitLabel}</span>}
            {onRestore && deleted.length > 0 && (
                <div className="unit-deleted">
                    <span className="lbl">Excluídas (restauráveis por 30 dias)</span>
                    {deleted.map((u) => (
                        <div key={u.code} className="unit-deleted-row">
                            <span className="unit-name">{u.name}</span>
                            <span className="unit-sub">{deletedSub(u)}</span>
                            <button
                                type="button"
                                className="btn btn-ghost small"
                                disabled={restoring !== null}
                                onClick={() => void restore(u.code)}
                            >
                                {restoring === u.code ? 'Restaurando…' : 'Restaurar'}
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </nav>
    )
}
