import { customRange, KIND, NEVER, NEVER_LABEL, PERIODS, type AuditFilter, type AuditPeriod } from './auditView.ts'
import { kindOptions } from '../../../services/auditEvents.ts'

// Tipos com evento, em ordem alfabética, e "Outros" no fim ("Nunca acessou" vem depois, à parte).
const KIND_OPTIONS = kindOptions()

type AuditFiltersProps = {
    value: AuditFilter
    actors: string[] // opções do campo Pessoa
    onChange: (next: AuditFilter) => void
}

// Módulo: os campos Período, Tipo de evento e Pessoa. Recebe o filtro atual e avisa quando muda.
export function AuditFilters({ value, actors, onChange }: AuditFiltersProps) {
    // Trocar de período: "Escolher datas" já começa com os últimos 7 dias; os outros limpam as datas.
    function setPeriod(period: AuditPeriod) {
        const dates = period === 'custom' ? customRange() : { de: '', ate: '' }
        onChange({ ...value, period, ...dates })
    }

    return (
        <div className="filters">
            <label className="filter">
                <span className="lbl">Período</span>
                <select
                    className="field"
                    value={value.period}
                    onChange={(e) => setPeriod(e.target.value as AuditPeriod)}
                >
                    {Object.entries(PERIODS).map(([key, label]) => (
                        <option key={key} value={key}>
                            {label}
                        </option>
                    ))}
                </select>
            </label>
            {value.period === 'custom' && (
                <>
                    {/* min/max impedem "de" depois de "até" (a URL voltaria para 7 dias). */}
                    <label className="filter">
                        <span className="lbl">De</span>
                        <input
                            className="field"
                            type="date"
                            value={value.de}
                            max={value.ate}
                            required
                            onChange={(e) => e.target.value && onChange({ ...value, de: e.target.value })}
                        />
                    </label>
                    <label className="filter">
                        <span className="lbl">Até</span>
                        <input
                            className="field"
                            type="date"
                            value={value.ate}
                            min={value.de}
                            required
                            onChange={(e) => e.target.value && onChange({ ...value, ate: e.target.value })}
                        />
                    </label>
                </>
            )}
            <label className="filter">
                <span className="lbl">Tipo de evento</span>
                <select
                    className="field"
                    value={value.kind}
                    onChange={(e) => onChange({ ...value, kind: e.target.value as AuditFilter['kind'] })}
                >
                    <option value="">Todos</option>
                    {KIND_OPTIONS.map((key) => (
                        <option key={key} value={key}>
                            {KIND[key].label}
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
