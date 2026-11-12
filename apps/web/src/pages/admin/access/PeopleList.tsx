import { useState } from 'react'
import { matchesText } from '../../../lib/text.ts'
import type { Member } from '../../../types/index.ts'
import { ROLE_LABEL } from '../members/memberView.ts'

const unitLabel = (code: string) => code.replace('_', ' ')

// "Gestor em NG · Leitor em LA AM" · "Desenvolvedor" · "Sem cargo"
function summaryOf(m: Member): string {
    if (m.org_role === 'owner' || m.org_role === 'admin') return ROLE_LABEL[m.org_role]
    if (m.units.length === 0) return 'Sem cargo'
    return m.units.map((u) => `${ROLE_LABEL[u.role]} em ${unitLabel(u.code)}`).join(' · ')
}

// Módulo: o card "Pessoas" — busca e lista compacta. Clicar avisa quem usa (que abre o editor).
export function PeopleList({ members, onPick }: { members: Member[]; onPick: (m: Member) => void }) {
    const [q, setQ] = useState('')
    const visible = members.filter((m) => matchesText(`${m.name} ${m.email}`, q))
    return (
        <section className="card people-card" aria-label="Pessoas">
            <div className="card-head" style={{ paddingBottom: 10 }}>
                <h2 className="h2">Pessoas</h2>
                <span className="muted small">{members.length} ativas</span>
            </div>
            <div style={{ padding: '0 14px 10px' }}>
                <input
                    className="field"
                    type="search"
                    placeholder="Nome ou e-mail"
                    aria-label="Buscar pessoa"
                    value={q}
                    onChange={(e) => setQ(e.target.value)}
                />
            </div>
            <ul className="people-list">
                {visible.length === 0 && <li className="muted small people-empty">Ninguém com essa busca.</li>}
                {visible.map((m) => (
                    <li key={m.id}>
                        <button type="button" className="people-row" onClick={() => onPick(m)}>
                            <span className="people-name">{m.name}</span>
                            <span className="muted small">{summaryOf(m)}</span>
                        </button>
                    </li>
                ))}
            </ul>
        </section>
    )
}
