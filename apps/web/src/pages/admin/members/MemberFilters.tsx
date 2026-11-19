import type { Unit } from '../../../types/index.ts'
import { ROLE_LABEL, STATUS_OPTIONS, type MemberFilter } from './memberView.ts'

type MemberFiltersProps = {
    value: MemberFilter
    units: Unit[] // opções do campo Unidade
    onChange: (next: MemberFilter) => void
}

// Módulo: os campos Buscar, Unidade, Cargo e Situação. Recebe o filtro atual e avisa quando muda;
// não sabe se o filtro fica na URL ou em outro lugar.
export function MemberFilters({ value, units, onChange }: MemberFiltersProps) {
    return (
        <div className="filters">
            <label className="filter-grow">
                <span className="lbl">Buscar</span>
                <input
                    className="field"
                    type="search"
                    placeholder="Nome, e-mail ou setor"
                    value={value.q}
                    onChange={(e) => onChange({ ...value, q: e.target.value })}
                />
            </label>
            <label className="filter">
                <span className="lbl">Unidade</span>
                <select
                    className="field"
                    value={value.unit}
                    onChange={(e) => onChange({ ...value, unit: e.target.value })}
                >
                    <option value="">Todas as unidades</option>
                    {units.map((u) => (
                        <option key={u.code} value={u.code}>
                            {u.name}
                        </option>
                    ))}
                </select>
            </label>
            <label className="filter">
                <span className="lbl">Cargo</span>
                <select
                    className="field"
                    value={value.role}
                    onChange={(e) => onChange({ ...value, role: e.target.value as MemberFilter['role'] })}
                >
                    <option value="">Todos</option>
                    {Object.entries(ROLE_LABEL).map(([key, label]) => (
                        <option key={key} value={key}>
                            {label}
                        </option>
                    ))}
                </select>
            </label>
            <label className="filter">
                <span className="lbl">Situação</span>
                <select
                    className="field"
                    value={value.status}
                    onChange={(e) => onChange({ ...value, status: e.target.value as MemberFilter['status'] })}
                >
                    <option value="">Todas</option>
                    {STATUS_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value}>
                            {o.label}
                        </option>
                    ))}
                </select>
            </label>
        </div>
    )
}
