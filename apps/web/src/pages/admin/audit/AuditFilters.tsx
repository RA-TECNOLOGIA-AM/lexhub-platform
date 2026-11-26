import { customRange, KIND, NEVER, NEVER_LABEL, PERIODS, type AuditFilter, type AuditPeriod } from './auditView.ts'
import { kindOptions } from '../../../services/auditEvents.ts'
import type { AuditResponse } from '../../../types/index.ts'
import { DateField } from '../../../components/ui/DateField.tsx'
import { todayIso } from '../../../lib/period.ts'

const KIND_OPTIONS = kindOptions()

// Opções do "Tipo de evento" depois de "Todos": tipos com evento, "Outros" e (quem pode) "Nunca acessou",
// tudo em ordem alfabética.
export function kindSelectOptions(allowNever: boolean): { value: string; label: string }[] {
    const options = KIND_OPTIONS.map((key) => ({ value: key as string, label: KIND[key].label }))
    if (allowNever) options.push({ value: NEVER, label: NEVER_LABEL })
    return options.sort((a, b) => a.label.localeCompare(b.label, 'pt-BR'))
}

type AuditFiltersProps = {
    value: AuditFilter
    actors: string[] // opções do campo Pessoa
    units: AuditResponse['units'] // opções do campo Unidade (excluídas também)
    orgs: AuditResponse['orgs'] // null = quem não é da plataforma (o campo Organização não aparece)
    currentOrg: string // a organização da URL (o valor de "org" vazio)
    allowNever: boolean // "Nunca acessou" só na organização da URL (lê os membros dela)
    onChange: (next: AuditFilter) => void
}

// Módulo: os campos Organização (só a plataforma), Unidade, Período, Tipo de evento e Pessoa.
// Recebe o filtro atual e avisa quando muda. Trocar de organização limpa unidade e pessoa (são de outra).
export function AuditFilters({ value, actors, units, orgs, currentOrg, allowNever, onChange }: AuditFiltersProps) {
    // Trocar de período: "Escolher datas" já começa com os últimos 7 dias; os outros limpam as datas.
    function setPeriod(period: AuditPeriod) {
        const dates = period === 'custom' ? customRange() : { de: '', ate: '' }
        onChange({ ...value, period, ...dates })
    }

    const org = value.org || currentOrg
    const today = todayIso()
    const range = { from: value.de, to: value.ate }
    return (
        <div className="filters">
            {orgs && (
                <label className="filter">
                    <span className="lbl">Organização</span>
                    <select
                        className="field"
                        value={org}
                        onChange={(e) =>
                            onChange({
                                ...value,
                                org: e.target.value === currentOrg ? '' : e.target.value,
                                unit: '',
                                actor: '',
                                kind: value.kind === NEVER ? '' : value.kind,
                            })
                        }
                    >
                        {orgs.map((o) => (
                            <option key={o.slug} value={o.slug}>
                                {o.closed ? `${o.name} (encerrada)` : o.name}
                            </option>
                        ))}
                    </select>
                </label>
            )}
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
                            {u.deleted ? `${u.name} (excluída)` : u.name}
                        </option>
                    ))}
                </select>
            </label>
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
                    <DateField
                        className="filter"
                        label="De"
                        value={value.de}
                        max={value.ate || today}
                        today={today}
                        range={range}
                        onChange={(de) => onChange({ ...value, de })}
                    />
                    <DateField
                        className="filter"
                        label="Até"
                        value={value.ate}
                        min={value.de}
                        max={today}
                        today={today}
                        range={range}
                        onChange={(ate) => onChange({ ...value, ate })}
                    />
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
                    {kindSelectOptions(allowNever).map((o) => (
                        <option key={o.value} value={o.value}>
                            {o.label}
                        </option>
                    ))}
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
