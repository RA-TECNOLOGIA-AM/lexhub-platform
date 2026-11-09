import type { RoleKey, Unit } from '../../../types/index.ts'
import { ROLE_LABEL, type MemberFilter } from './memberView.ts'

type MemberFiltersProps = {
    value: MemberFilter
    units: Unit[] // opções do campo Unidade
    onChange: (next: MemberFilter) => void
}

// Módulo: os campos Buscar, Unidade e Papel. Recebe o filtro atual e avisa quando muda;
// não sabe se o filtro fica na URL ou em outro lugar.
export function MemberFilters({ value, units, onChange }: MemberFiltersProps) {
    return (
        <div className="filters">
            <label className="filter-grow">
                <span className="lbl">Buscar</span>
                <input
                    className="field"
                    type="search"
                    placeholder="Nome ou e-mail"
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
                    <option value="">Todas</option>
                    {units.map((u) => (
                        <option key={u.code} value={u.code}>
                            {u.name}
                        </option>
                    ))}
                </select>
            </label>
            <label className="filter">
                <span className="lbl">Papel</span>
                <select
                    className="field"
                    value={value.role}
                    onChange={(e) => onChange({ ...value, role: e.target.value as RoleKey | '' })}
                >
                    <option value="">Todos</option>
                    {Object.entries(ROLE_LABEL).map(([key, label]) => (
                        <option key={key} value={key}>
                            {label}
                        </option>
                    ))}
                </select>
            </label>
        </div>
    )
}
