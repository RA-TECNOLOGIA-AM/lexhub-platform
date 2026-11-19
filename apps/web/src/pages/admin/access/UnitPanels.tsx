import { useState } from 'react'
import type { AccessOverview, UnitRoleKey } from '../../../types/index.ts'
import { ROLE_LABEL } from '../members/memberView.ts'
import {
    avulsoOptions,
    roleSeesAll,
    sectorCoverage,
    setAllTeams,
    setUnitRole,
    toggleExtraDashboard,
    toggleExtraGroup,
    toggleTeam,
    type AccessDraft,
} from './accessEditor.ts'

// Os três painéis de uma unidade no editor da pessoa: Cargo e setores · Grupos extras · Dashboards avulsos.
// Cada um recebe o rascunho e devolve o rascunho novo (onChange); nada grava até o Salvar.

type PanelProps = {
    overview: AccessOverview
    draft: AccessDraft
    unit: string
    readOnly: boolean
    onChange: (draft: AccessDraft) => void
}

const UNIT_ROLES: UnitRoleKey[] = ['gestor', 'controller', 'colaborador', 'leitor']

function PanelHead({ title, hint, tag }: { title: string; hint: string; tag?: string }) {
    return (
        <div className="acc-panel-head">
            <div>
                <h3 className="acc-panel-title">{title}</h3>
                <span className="muted small">{hint}</span>
            </div>
            {tag && <span className="badge neutral">{tag}</span>}
        </div>
    )
}

// Por que as exceções não fazem diferença nesta unidade (null = fazem).
function exceptionsBlocked(overview: AccessOverview, draft: AccessDraft, unit: string): string | null {
    const role = draft.units[unit] ?? ''
    if (draft.orgRole === 'owner') return 'Já vê tudo como Owner.'
    if (draft.orgRole === 'admin') return 'Já vê tudo como Desenvolvedor.'
    if (!role) return 'Escolha um cargo nesta unidade para liberar exceções.'
    if (roleSeesAll(overview, role)) return `Já vê tudo nesta unidade como ${ROLE_LABEL[role]}.`
    if (sectorCoverage(overview, draft, unit).all) return 'Um setor marcado já vê tudo nesta unidade.'
    return null
}

export function SectorsPanel({ overview, draft, unit, readOnly, onChange }: PanelProps) {
    const role = draft.units[unit] ?? ''
    const unitName = overview.units.find((u) => u.code === unit)?.name ?? unit
    const teams = overview.teams.filter((t) => t.unit === unit)
    const marked = teams.filter((t) => draft.teams.includes(t.id)).length
    const all = teams.length > 0 && marked === teams.length
    return (
        <section className="acc-panel acc-panel-sectors" aria-label="Cargo e setores">
            <div className="acc-panel-head">
                <div>
                    <h3 className="acc-panel-title">Cargo e setores</h3>
                    <span className="muted small">{unitName}</span>
                </div>
                <select
                    className="field acc-role"
                    aria-label={`Cargo em ${unitName}`}
                    value={role}
                    disabled={readOnly}
                    onChange={(e) =>
                        onChange(setUnitRole(draft, unit, e.target.value as UnitRoleKey | '', overview.teams))
                    }
                >
                    <option value="">Sem cargo</option>
                    {UNIT_ROLES.map((r) => (
                        <option key={r} value={r}>
                            {ROLE_LABEL[r]}
                        </option>
                    ))}
                </select>
            </div>
            {!role && (
                <p className="acc-empty muted small">
                    Sem cargo em <strong>{unitName}</strong>. Escolha um cargo para marcar setores e exceções.
                </p>
            )}
            {role && teams.length === 0 && <p className="acc-empty muted small">Nenhum setor nesta unidade.</p>}
            {role && teams.length > 0 && (
                <>
                    <div className="acc-subhead">
                        <span className="muted small">
                            Setores ({marked}/{teams.length})
                        </span>
                        {!readOnly && (
                            <button
                                type="button"
                                className="linkbtn small"
                                onClick={() => onChange(setAllTeams(draft, unit, overview.teams, !all))}
                            >
                                {all ? 'Limpar todos' : 'Selecionar todos'}
                            </button>
                        )}
                    </div>
                    <div className="acc-options acc-options-2">
                        {teams.map((t) => {
                            const on = draft.teams.includes(t.id)
                            return (
                                <label key={t.id} className={on ? 'acc-option on' : 'acc-option'}>
                                    <input
                                        type="checkbox"
                                        checked={on}
                                        disabled={readOnly}
                                        onChange={() => onChange(toggleTeam(draft, t.id))}
                                    />
                                    <span>{t.name}</span>
                                    {t.sees_all && <span className="muted small">vê tudo</span>}
                                </label>
                            )
                        })}
                    </div>
                </>
            )}
        </section>
    )
}

export function ExtraGroupsPanel({ overview, draft, unit, readOnly, onChange }: PanelProps) {
    const blocked = exceptionsBlocked(overview, draft, unit)
    const cov = sectorCoverage(overview, draft, unit)
    const groups = draft.extraGroups[unit] ?? []
    return (
        <section className="acc-panel" aria-label="Grupos extras">
            <PanelHead title="Grupos extras" hint="A coluna inteira do hub" tag="só visualiza" />
            {blocked ? (
                <p className="acc-empty muted small">{blocked}</p>
            ) : (
                <div className="acc-options">
                    {overview.groups.map((g) => {
                        const by = cov.groups.get(g.slug)
                        const on = Boolean(by) || groups.includes(g.slug)
                        return (
                            <label
                                key={g.slug}
                                className={on ? 'acc-option acc-option-switch on' : 'acc-option acc-option-switch'}
                                title={by ? `Pelo setor ${by.join(', ')} (vê e exporta)` : undefined}
                            >
                                <span>{g.name}</span>
                                {by && <span className="muted small">setor</span>}
                                <input
                                    type="checkbox"
                                    role="switch"
                                    className="acc-switch"
                                    checked={on}
                                    disabled={readOnly || Boolean(by)}
                                    onChange={() => onChange(toggleExtraGroup(draft, unit, g.slug))}
                                />
                            </label>
                        )
                    })}
                </div>
            )}
        </section>
    )
}

export function AvulsosPanel({ overview, draft, unit, readOnly, onChange }: PanelProps) {
    const [query, setQuery] = useState('')
    const blocked = exceptionsBlocked(overview, draft, unit)
    const chosen = draft.extraDashboards[unit] ?? []
    const { options, covered } = avulsoOptions(overview, draft, unit)
    const q = query.trim().toLowerCase()
    const shown = options.filter((o) => !q || o.title.toLowerCase().includes(q))
    const groupName = (slug: string) => overview.groups.find((g) => g.slug === slug)?.name ?? slug
    const title = (key: string) => overview.titles[key] ?? key
    // avulso salvo que um setor ou grupo passou a cobrir: continua salvo, mas avisa
    const redundant = chosen.filter((k) => !options.some((o) => o.key === k))
    return (
        <section className="acc-panel" aria-label="Dashboards avulsos">
            <PanelHead
                title="Dashboards avulsos"
                hint={`Liberação pontual (${chosen.length} ${chosen.length === 1 ? 'ativo' : 'ativos'})`}
                tag="só visualiza"
            />
            {blocked ? (
                <p className="acc-empty muted small">{blocked}</p>
            ) : (
                <>
                    <input
                        className="field"
                        type="search"
                        placeholder="Buscar dashboard"
                        aria-label="Buscar dashboard avulso"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <div className="acc-avulsos">
                        {shown.map((o, i) => (
                            <div key={o.key}>
                                {(i === 0 || shown[i - 1].group !== o.group) && (
                                    <span className="acc-group-label">{groupName(o.group)}</span>
                                )}
                                <label className={chosen.includes(o.key) ? 'acc-option on' : 'acc-option'}>
                                    <input
                                        type="checkbox"
                                        checked={chosen.includes(o.key)}
                                        disabled={readOnly}
                                        onChange={() => onChange(toggleExtraDashboard(draft, unit, o.key))}
                                    />
                                    <span>{o.title}</span>
                                </label>
                            </div>
                        ))}
                        {shown.length === 0 && <span className="muted small">Nada para liberar.</span>}
                    </div>
                    {redundant.length > 0 && (
                        <div className="tags" aria-label="Avulsos já cobertos">
                            <span className="muted small">Já coberto pelo setor ou por um grupo:</span>
                            {redundant.map((k) => (
                                <button
                                    key={k}
                                    type="button"
                                    className="tag acc-tag-x"
                                    disabled={readOnly}
                                    aria-label={`Tirar ${title(k)}`}
                                    onClick={() => onChange(toggleExtraDashboard(draft, unit, k))}
                                >
                                    {title(k)} ×
                                </button>
                            ))}
                        </div>
                    )}
                    {covered > 0 && (
                        <span className="muted small">{covered} já cobertos pelo setor ou por grupos.</span>
                    )}
                </>
            )}
        </section>
    )
}
