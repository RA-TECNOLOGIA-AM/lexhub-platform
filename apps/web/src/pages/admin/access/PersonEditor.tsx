import { useEffect, useState } from 'react'
import { toDataError } from '../../../services/errors.ts'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import type { AccessOverview, Member, MemberAccessUpdate, OrgRoleKey } from '../../../types/index.ts'
import { ROLE_LABEL } from '../members/memberView.ts'
import {
    draftFromMember,
    firstUnit,
    isDirty,
    personalText,
    previewDashboards,
    previewText,
    readOnlyReason,
    toUpdate,
    unitHasAccess,
} from './accessEditor.ts'
import { AvulsosPanel, ExtraGroupsPanel, SectorsPanel } from './UnitPanels.tsx'

type PersonEditorProps = {
    member: Member
    overview: AccessOverview
    isSelf: boolean
    onSave: (update: MemberAccessUpdate) => Promise<void>
    onDirtyChange: (dirty: boolean) => void // a página pergunta antes de trocar de pessoa ou de aba
}

const ORG_ROLE_OPTIONS: { value: OrgRoleKey; label: string }[] = [
    { value: 'member', label: 'Membro' },
    { value: 'admin', label: 'Desenvolvedor' },
    { value: 'owner', label: 'Owner' },
]

const ORG_ROLE_HINT: Record<OrgRoleKey, string> = {
    member: 'Vê o que os cargos nas unidades liberam.',
    admin: 'Vê e gere todas as unidades.',
    owner: 'Vê e gere tudo. Depois de salvo, só um Owner tira o papel de Owner.',
}

const initials = (name: string) =>
    name
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((w) => w[0])
        .join('')
        .toUpperCase()

// Módulo: o detalhe da pessoa na aba Pessoas — cabeçalho (Descartar/Salvar), Desenvolvedor,
// abas por unidade e, na unidade escolhida, Cargo e setores · Grupos extras · Dashboards avulsos.
// Embaixo, o que ela passa a ver em cada unidade. Edita um rascunho; nada muda até o Salvar.
// Quem usa remonta o componente (key) depois de salvar, para o rascunho partir do que o banco devolveu.
export function PersonEditor({ member, overview, isSelf, onSave, onDirtyChange }: PersonEditorProps) {
    const [original] = useState(() => draftFromMember(member, overview))
    const [draft, setDraft] = useState(original)
    const codes = overview.units.map((u) => u.code)
    const [unit, setUnit] = useState(() => firstUnit(original, codes))
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const readOnlyText = readOnlyReason(member, overview, isSelf)
    const readOnly = readOnlyText !== null || saving
    const dirty = isDirty(original, draft)
    useEffect(() => onDirtyChange(dirty), [dirty, onDirtyChange])
    useEffect(() => () => onDirtyChange(false), [onDirtyChange]) // saiu da tela: nada pendente

    async function save() {
        setSaving(true)
        setError(null)
        try {
            await onSave(toUpdate(draft, original, overview.can_set_org_role))
        } catch (err) {
            setError(toDataError(err).message)
            setSaving(false)
        }
    }

    const unitName = (code: string) => overview.units.find((u) => u.code === code)?.name ?? code
    const preview = previewDashboards(overview, draft)
    const isDev = draft.orgRole === 'admin' || draft.orgRole === 'owner'
    const panel = { overview, draft, unit, readOnly, onChange: setDraft }

    return (
        <section className="card acc-detail" aria-label={`Acesso de ${member.name}`}>
            <header className="acc-detail-head">
                <div className="acc-person">
                    <span className="av acc-av">{initials(member.name)}</span>
                    <div style={{ minWidth: 0 }}>
                        <div className="row" style={{ gap: 8 }}>
                            <h2 className="h2 acc-person-name">{member.name}</h2>
                            {dirty && <span className="badge warn">Não salvo</span>}
                        </div>
                        <span className="muted small acc-person-email">{member.email}</span>
                    </div>
                </div>
                {readOnlyText === null && (
                    <div className="row" style={{ flexWrap: 'nowrap' }}>
                        <button
                            className="btn"
                            type="button"
                            disabled={!dirty || saving}
                            onClick={() => setDraft(original)}
                        >
                            Descartar
                        </button>
                        <button className="btn btn-primary" type="button" disabled={!dirty || saving} onClick={save}>
                            {saving ? 'Salvando…' : 'Salvar alterações'}
                        </button>
                    </div>
                )}
            </header>

            {readOnlyText && <p className="acc-note muted small">{readOnlyText}</p>}
            {error && (
                <p className="invite-error acc-note" role="alert">
                    {error}
                </p>
            )}

            {overview.can_set_org_role && member.org_role !== 'owner' && (
                <div className="acc-dev">
                    <div className="acc-dev-label">
                        <span>Papel na organização</span>
                        {isSelf || readOnly ? (
                            <span className="badge">{ORG_ROLE_OPTIONS.find((o) => o.value === draft.orgRole)?.label}</span>
                        ) : (
                            <Segmented
                                label="Papel na organização"
                                options={ORG_ROLE_OPTIONS}
                                value={draft.orgRole}
                                onChange={(orgRole) => setDraft({ ...draft, orgRole })}
                            />
                        )}
                    </div>
                    {isSelf ? (
                        <span className="muted small">Você não muda o próprio papel.</span>
                    ) : draft.orgRole === 'owner' ? (
                        <span className="small acc-dev-warn">{ORG_ROLE_HINT.owner}</span>
                    ) : (
                        <span className="muted small">{ORG_ROLE_HINT[draft.orgRole]}</span>
                    )}
                </div>
            )}

            <div className="acc-tabs" role="tablist" aria-label="Unidades">
                {overview.units.map((u) => {
                    const role = draft.units[u.code]
                    return (
                        <button
                            key={u.code}
                            type="button"
                            role="tab"
                            aria-selected={u.code === unit}
                            className={u.code === unit ? 'acc-tab on' : 'acc-tab'}
                            onClick={() => setUnit(u.code)}
                        >
                            <span className={unitHasAccess(draft, u.code) ? 'acc-dot on' : 'acc-dot'} aria-hidden />
                            {u.name}
                            {role && <span className="acc-tab-role">{ROLE_LABEL[role]}</span>}
                        </button>
                    )
                })}
            </div>

            <div className="acc-body" role="tabpanel" aria-label={unitName(unit)}>
                {isDev && (
                    <p className="acc-note muted small">
                        Como {draft.orgRole === 'owner' ? 'Owner' : 'Desenvolvedor'}, {member.name} já vê tudo em todas
                        as unidades. O que está abaixo só vale se o papel for tirado.
                    </p>
                )}
                <div className={isDev ? 'acc-panels is-muted' : 'acc-panels'}>
                    <SectorsPanel {...panel} />
                    <ExtraGroupsPanel {...panel} />
                    <AvulsosPanel key={unit} {...panel} />
                </div>

                <div className="invite-preview stack acc-preview" style={{ gap: 6 }} aria-live="polite">
                    <span style={{ fontWeight: 500 }}>O que passa a ver</span>
                    {preview.length === 0 && <span>Nenhum dashboard: sem cargo em nenhuma unidade.</span>}
                    {preview.map((p) => (
                        <span key={p.unit}>
                            <strong>{unitName(p.unit)}</strong>: {previewText(p)}
                            {personalText(p) && (
                                <span className="muted" style={{ display: 'block' }}>
                                    {personalText(p)}
                                </span>
                            )}
                        </span>
                    ))}
                </div>
            </div>
        </section>
    )
}
