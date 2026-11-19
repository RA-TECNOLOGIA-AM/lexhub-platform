import { useState } from 'react'
import { toDataError } from '../../../services/errors.ts'
import type { AccessOverview, AccessTeam } from '../../../types/index.ts'

type SectorGroupsProps = {
    overview: AccessOverview
    // Grava os grupos do setor (estado desejado) e, quando não é null, o "vê tudo". A página busca de novo.
    onSave: (teamId: string, groups: string[], seesAll: boolean | null) => Promise<void>
}

// Módulo: "Grupos dos setores" da unidade da página. Cada setor libera colunas inteiras do hub
// (grupos) para quem está nele, além das regras card a card; "Vê tudo" (Diretoria) libera a unidade
// inteira e só Owner/Desenvolvedor muda. Tudo o que vem do setor vê e exporta (se o cargo exporta).
// Cada clique grava na hora (como liga/desliga de dashboard); erro aparece embaixo da tabela.
export function SectorGroups({ overview, onSave }: SectorGroupsProps) {
    const [pending, setPending] = useState<string | null>(null) // setor gravando
    const [error, setError] = useState<string | null>(null)
    // O que já foi gravado e ainda não voltou na busca de novo (vale só sobre a overview em que foi
    // gravado): a caixa não pisca para o valor antigo. A overview nova já traz o valor do banco.
    type Saved = { base: AccessOverview; teams: Record<string, Pick<AccessTeam, 'groups' | 'sees_all'>> }
    const [saved, setSaved] = useState<Saved | null>(null)
    const pendingTeams = saved?.base === overview ? saved.teams : {}
    const teams = overview.teams.filter((t) => t.unit === overview.unit).map((t) => ({ ...t, ...pendingTeams[t.id] }))
    const unitName = overview.units.find((u) => u.code === overview.unit)?.name ?? overview.unit

    async function save(team: AccessTeam, groups: string[], seesAll: boolean | null) {
        setPending(team.id)
        setError(null)
        try {
            await onSave(team.id, groups, seesAll)
            setSaved((s) => ({
                base: overview,
                teams: {
                    ...(s?.base === overview ? s.teams : {}),
                    [team.id]: { groups, sees_all: seesAll ?? team.sees_all },
                },
            }))
        } catch (err) {
            setError(`${team.name}: ${toDataError(err).message}`)
        } finally {
            setPending(null)
        }
    }

    const toggleGroup = (team: AccessTeam, slug: string) =>
        save(team, team.groups.includes(slug) ? team.groups.filter((g) => g !== slug) : [...team.groups, slug], null)

    return (
        <section className="card" style={{ overflow: 'hidden' }} aria-label="Grupos dos setores">
            <div className="card-head" style={{ paddingBottom: 4 }}>
                <h2 className="h2">Grupos dos setores em {unitName}</h2>
            </div>
            <p className="muted small" style={{ margin: '0 18px 12px' }}>
                Um grupo libera a coluna inteira do hub para quem está no setor, inclusive os dashboards que vierem
                depois. O que vem do setor pode ser exportado (se o cargo exporta).
            </p>
            {teams.length === 0 ? (
                <p className="muted" style={{ margin: '0 18px 18px' }}>
                    Nenhum setor nesta unidade.
                </p>
            ) : (
                <div className="tblwrap">
                    <table className="tbl" style={{ minWidth: 640 }}>
                        <thead>
                            <tr>
                                <th>Setor</th>
                                <th className="center">Vê tudo</th>
                                {overview.groups.map((g) => (
                                    <th key={g.slug} className="center">
                                        {g.name}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {teams.map((t) => {
                                const busy = pending !== null
                                return (
                                    <tr key={t.id} aria-busy={pending === t.id}>
                                        <td style={{ fontWeight: 500 }}>{t.name}</td>
                                        <td className="center">
                                            <input
                                                type="checkbox"
                                                aria-label={`${t.name} vê tudo`}
                                                checked={t.sees_all}
                                                disabled={busy || !overview.can_set_org_role}
                                                title={
                                                    overview.can_set_org_role
                                                        ? undefined
                                                        : 'Só Owner ou Desenvolvedor muda quem vê tudo.'
                                                }
                                                onChange={() => save(t, t.groups, !t.sees_all)}
                                            />
                                        </td>
                                        {overview.groups.map((g) => (
                                            <td key={g.slug} className="center">
                                                <input
                                                    type="checkbox"
                                                    aria-label={`${t.name}: ${g.name}`}
                                                    checked={t.sees_all || t.groups.includes(g.slug)}
                                                    disabled={busy || t.sees_all}
                                                    onChange={() => toggleGroup(t, g.slug)}
                                                />
                                            </td>
                                        ))}
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </div>
            )}
            {error && (
                <p className="invite-error" role="alert" style={{ margin: '0 18px 18px' }}>
                    {error}
                </p>
            )}
        </section>
    )
}
