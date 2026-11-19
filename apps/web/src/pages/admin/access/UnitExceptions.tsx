import { useState } from 'react'
import type { AccessOverview } from '../../../types/index.ts'
import {
    avulsoOptions,
    sectorCoverage,
    toggleExtraDashboard,
    toggleExtraGroup,
    type AccessDraft,
} from './accessEditor.ts'

type UnitExceptionsProps = {
    overview: AccessOverview
    draft: AccessDraft
    unit: string
    readOnly: boolean
    onChange: (draft: AccessDraft) => void
}

// Módulo: as exceções de uma pessoa numa unidade (dentro do cartão da unidade, no modal de acesso).
// Grupos extras = colunas inteiras; avulsos = dashboards soltos. As duas só liberam visualização.
// O que os setores marcados já dão aparece marcado e travado (grupo) ou fica de fora da lista (avulso).
export function UnitExceptions({ overview, draft, unit, readOnly, onChange }: UnitExceptionsProps) {
    const [query, setQuery] = useState('')
    const cov = sectorCoverage(overview, draft, unit)
    if (cov.all) return <span className="muted small">O setor já vê tudo nesta unidade.</span>

    const groups = draft.extraGroups[unit] ?? []
    const chosen = draft.extraDashboards[unit] ?? []
    const { options, covered } = avulsoOptions(overview, draft, unit)
    const q = query.trim().toLowerCase()
    const shown = options.filter((o) => !q || o.title.toLowerCase().includes(q))
    const groupName = (slug: string) => overview.groups.find((g) => g.slug === slug)?.name ?? slug
    const title = (key: string) => overview.titles[key] ?? key
    // avulso escolhido que um setor ou grupo passou a cobrir: segue salvo, mas avisa
    const redundant = chosen.filter((k) => !options.some((o) => o.key === k))

    return (
        <div className="unit-exceptions">
            <span className="unit-exceptions-title">Grupos extras · só visualiza</span>
            <div className="unit-teams">
                {overview.groups.map((g) => {
                    const by = cov.groups.get(g.slug)
                    return (
                        <label key={g.slug} className="check" title={by ? `Pelo setor ${by.join(', ')}` : undefined}>
                            <input
                                type="checkbox"
                                checked={Boolean(by) || groups.includes(g.slug)}
                                disabled={readOnly || Boolean(by)}
                                onChange={() => onChange(toggleExtraGroup(draft, unit, g.slug))}
                            />
                            {g.name}
                            {by && <span className="muted small">(setor)</span>}
                        </label>
                    )
                })}
            </div>

            <details className="unit-avulsos">
                <summary>Dashboards avulsos · só visualiza{chosen.length > 0 && ` (${chosen.length})`}</summary>
                {chosen.length > 0 && (
                    <div className="pills" style={{ gap: 4 }}>
                        {chosen.map((k) => (
                            <button
                                key={k}
                                type="button"
                                className="tag"
                                disabled={readOnly}
                                aria-label={`Tirar ${title(k)}`}
                                onClick={() => onChange(toggleExtraDashboard(draft, unit, k))}
                            >
                                {title(k)} ×
                            </button>
                        ))}
                    </div>
                )}
                {redundant.length > 0 && (
                    <span className="muted small">
                        Já coberto pelo setor ou por um grupo: {redundant.map(title).join(', ')}
                    </span>
                )}
                <input
                    className="field"
                    type="search"
                    placeholder="Buscar dashboard"
                    aria-label={`Buscar dashboard avulso em ${unit}`}
                    value={query}
                    disabled={readOnly}
                    onChange={(e) => setQuery(e.target.value)}
                />
                <div className="unit-avulsos-list">
                    {shown.map((o, i) => (
                        <div key={o.key}>
                            {(i === 0 || shown[i - 1].group !== o.group) && (
                                <span className="muted small">{groupName(o.group)}</span>
                            )}
                            <label className="check">
                                <input
                                    type="checkbox"
                                    checked={chosen.includes(o.key)}
                                    disabled={readOnly}
                                    onChange={() => onChange(toggleExtraDashboard(draft, unit, o.key))}
                                />
                                {o.title}
                            </label>
                        </div>
                    ))}
                    {shown.length === 0 && <span className="muted small">Nada para liberar.</span>}
                </div>
                {covered > 0 && <span className="muted small">{covered} já cobertos pelo setor ou por grupos.</span>}
            </details>
        </div>
    )
}
