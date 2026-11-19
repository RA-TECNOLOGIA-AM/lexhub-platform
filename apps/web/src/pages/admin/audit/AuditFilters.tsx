import { KIND, NEVER, NEVER_LABEL, type AuditFilter } from './auditView.ts'

type AuditFiltersProps = {
    value: AuditFilter
    actors: string[] // opções do campo Pessoa
    onChange: (next: AuditFilter) => void
}

// Módulo: os campos Tipo de evento e Pessoa. Recebe o filtro atual e avisa quando muda.
export function AuditFilters({ value, actors, onChange }: AuditFiltersProps) {
    return (
        <div className="filters">
            <label className="filter">
                <span className="lbl">Tipo de evento</span>
                <select
                    className="field"
                    value={value.kind}
                    onChange={(e) => onChange({ ...value, kind: e.target.value as AuditFilter['kind'] })}
                >
                    <option value="">Todos</option>
                    {Object.entries(KIND).map(([key, k]) => (
                        <option key={key} value={key}>
                            {k.label}
                        </option>
                    ))}
                    <option value={NEVER}>{NEVER_LABEL}</option>
                </select>
            </label>
            <label className="filter">
                <span className="lbl">Pessoa</span>
                <select
                    className="field"
                    value={value.actor}
                    onChange={(e) => onChange({ ...value, actor: e.target.value })}
                >
                    <option value="">Todas</option>
                    {actors.map((a) => (
                        <option key={a} value={a}>
                            {a}
                        </option>
                    ))}
                </select>
            </label>
        </div>
    )
}
