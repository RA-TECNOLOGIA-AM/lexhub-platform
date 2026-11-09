import { useState } from 'react'
import type { Member, Permission, TeamRule, Unit } from '../../../types/index.ts'
import { simulateAccess } from './accessView.ts'

type AccessSimulatorProps = {
    members: Member[]
    rules: TeamRule[]
    matrix: Permission[]
    units: Unit[]
}

// Módulo: "Simular acesso". Escolhe uma pessoa e mostra o que ela vê, usando a regra do accessView.
export function AccessSimulator({ members, rules, matrix, units }: AccessSimulatorProps) {
    const [selectedId, setSelectedId] = useState(members[0]?.id ?? '')
    const selected = members.find((m) => m.id === selectedId)
    const sim = selected ? simulateAccess(selected, rules, matrix, units) : null

    return (
        <section className="card card-pad stack access-side" style={{ gap: 12 }} aria-label="Simular acesso">
            <h2 className="h2">Simular acesso</h2>
            <div className="pills" role="group" aria-label="Escolher pessoa">
                {members.map((m) => (
                    <button
                        key={m.id}
                        className="pill"
                        type="button"
                        aria-pressed={m.id === selectedId}
                        onClick={() => setSelectedId(m.id)}
                    >
                        {m.name ?? m.email}
                    </button>
                ))}
            </div>
            {sim && (
                <>
                    <span className="muted small">{sim.profile}</span>
                    <span>{sim.summary}</span>
                    <div className="tags">
                        {sim.dashboards.map((d) => (
                            <span key={d} className="tag">
                                {d}
                            </span>
                        ))}
                    </div>
                </>
            )}
        </section>
    )
}
