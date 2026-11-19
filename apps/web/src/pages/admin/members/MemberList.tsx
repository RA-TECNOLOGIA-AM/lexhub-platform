import type { Unit } from '../../../types/index.ts'
import { ROLE_LABEL, rowKey, statusOf, summaryOf, type MemberFilter, type MemberRow } from './memberView.ts'

type MemberListProps = {
    rows: MemberRow[] // já filtradas
    total: number // membros ativos (o número do cabeçalho)
    filter: MemberFilter
    units: Unit[] // opções do campo Unidade
    selectedKey: string | null // a linha aberta no detalhe (destacada)
    now: Date // para "vence em N dias"
    onFilter: (next: MemberFilter) => void
    onPick: (row: MemberRow) => void
}

// Módulo: a coluna "Pessoas" de Membros — busca, Unidade, Papel e a lista compacta
// (membros e convites). Não sabe onde o filtro fica guardado nem o que o clique abre.
export function MemberList({ rows, total, filter, units, selectedKey, now, onFilter, onPick }: MemberListProps) {
    return (
        <section className="card people-card" aria-label="Pessoas">
            <div className="card-head" style={{ paddingBottom: 10 }}>
                <h2 className="h2">Pessoas</h2>
                <span className="muted small">{total} ativas</span>
            </div>
            <div className="mem-filters">
                <input
                    className="field"
                    type="search"
                    placeholder="Nome ou e-mail"
                    aria-label="Buscar pessoa"
                    value={filter.q}
                    onChange={(e) => onFilter({ ...filter, q: e.target.value })}
                />
                <div className="mem-filters-row">
                    <select
                        className="field"
                        aria-label="Unidade"
                        value={filter.unit}
                        onChange={(e) => onFilter({ ...filter, unit: e.target.value })}
                    >
                        <option value="">Unidades</option>
                        {units.map((u) => (
                            <option key={u.code} value={u.code}>
                                {u.name}
                            </option>
                        ))}
                    </select>
                    <select
                        className="field"
                        aria-label="Papel"
                        value={filter.role}
                        onChange={(e) => onFilter({ ...filter, role: e.target.value as MemberFilter['role'] })}
                    >
                        <option value="">Papéis</option>
                        {Object.entries(ROLE_LABEL).map(([key, label]) => (
                            <option key={key} value={key}>
                                {label}
                            </option>
                        ))}
                    </select>
                </div>
            </div>
            <ul className="people-list">
                {rows.length === 0 && <li className="muted small people-empty">Ninguém com esses filtros.</li>}
                {rows.map((row) => {
                    const key = rowKey(row)
                    const on = key === selectedKey
                    const status = statusOf(row)
                    const active = row.kind === 'member' && row.member.status === 'active'
                    return (
                        <li key={key}>
                            <button
                                type="button"
                                className={on ? 'people-row on' : 'people-row'}
                                aria-current={on ? 'true' : undefined}
                                onClick={() => onPick(row)}
                            >
                                <span className="mem-row-top">
                                    <span className="people-name">
                                        {row.kind === 'member' ? row.member.name : row.invitation.email}
                                    </span>
                                    {!active && <span className={status.badge}>{status.label}</span>}
                                </span>
                                <span className="muted small">{summaryOf(row, now)}</span>
                            </button>
                        </li>
                    )
                })}
            </ul>
        </section>
    )
}
