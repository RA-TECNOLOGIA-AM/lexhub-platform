import { useState } from 'react'
import { Link } from 'react-router'
import { toDataError } from '../../../services/errors.ts'
import type { MemberTeam, Unit } from '../../../types/index.ts'
import { CopyLink } from './CopyLink.tsx'
import { inviteLink } from './invite.ts'
import { MemberAvatar } from './MemberAvatar.tsx'
import {
    firstUnitOf,
    hasUnitAccess,
    isOnline,
    lastSeenText,
    nameOf,
    noteOf,
    ROLE_LABEL,
    statusOf,
    unitViewOf,
    type MemberRow,
} from './memberView.ts'

type MemberDetailProps = {
    row: MemberRow
    units: Unit[] // as abas: unidades que quem vê gere
    teams: MemberTeam[] // para dar nome aos setores de cada unidade
    isSelf: boolean // a própria pessoa não se desativa
    accessHref: string // onde se editam cargos, setores e exceções (aba Acesso)
    onSetStatus: (status: 'active' | 'disabled') => Promise<void>
    onRevoke: () => Promise<void>
}

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`

// Módulo: o detalhe de uma pessoa (ou convite) em Membros — cabeçalho com a situação e as ações
// (Desativar/Reativar ou Cancelar convite), abas por unidade e, na unidade escolhida, cargo, setores
// e exceções só para leitura. Editar fica na aba Acesso (accessHref). Quem usa remonta pelo key.
export function MemberDetail({ row, units, teams, isSelf, accessHref, onSetStatus, onRevoke }: MemberDetailProps) {
    const codes = units.map((u) => u.code)
    const [unit, setUnit] = useState(() => firstUnitOf(row, codes, teams))
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [now] = useState(() => new Date())

    async function run(question: string, action: () => Promise<void>) {
        if (!window.confirm(question)) return
        setBusy(true)
        setError(null)
        try {
            await action()
        } catch (err) {
            setError(toDataError(err).message)
        } finally {
            setBusy(false)
        }
    }

    const status = statusOf(row)
    const orgWide =
        row.kind === 'member'
            ? row.member.org_role !== 'member' && ROLE_LABEL[row.member.org_role]
            : row.invitation.role === 'admin' && ROLE_LABEL.admin
    const view = unitViewOf(row, unit, teams)
    const unitName = units.find((u) => u.code === unit)?.name ?? unit

    return (
        <section className="card acc-detail" aria-label={`Detalhes de ${nameOf(row)}`}>
            <header className="acc-detail-head">
                <div className="acc-person">
                    <MemberAvatar row={row} now={now} className="acc-av" />
                    <div style={{ minWidth: 0 }}>
                        <div className="row" style={{ gap: 8 }}>
                            <h2 className="h2 acc-person-name">{nameOf(row)}</h2>
                            <span className={status.badge}>{status.label}</span>
                        </div>
                        <span className="muted small acc-person-email">{noteOf(row, now)}</span>
                        {row.kind === 'member' && (
                            <span
                                className={
                                    isOnline(row, now) ? 'small mem-presence mem-online' : 'muted small mem-presence'
                                }
                            >
                                {lastSeenText(row, now)}
                            </span>
                        )}
                    </div>
                </div>
                <div className="row" style={{ flexWrap: 'nowrap' }}>
                    {row.kind === 'member' ? (
                        <>
                            {!isSelf &&
                                (row.member.status === 'disabled' ? (
                                    <button
                                        className="btn"
                                        type="button"
                                        disabled={busy}
                                        onClick={() => run(`Reativar ${row.member.name}?`, () => onSetStatus('active'))}
                                    >
                                        Reativar
                                    </button>
                                ) : (
                                    <button
                                        className="btn"
                                        type="button"
                                        disabled={busy}
                                        onClick={() =>
                                            run(
                                                `Desativar ${row.member.name}? A pessoa deixa de entrar no LexHub até ser reativada.`,
                                                () => onSetStatus('disabled'),
                                            )
                                        }
                                    >
                                        Desativar
                                    </button>
                                ))}
                            <Link className="btn btn-primary" to={accessHref}>
                                Editar acesso
                            </Link>
                        </>
                    ) : (
                        row.invitation.can_revoke && (
                            <button
                                className="btn"
                                type="button"
                                disabled={busy}
                                onClick={() => run(`Cancelar o convite de ${row.invitation.email}?`, onRevoke)}
                            >
                                Cancelar convite
                            </button>
                        )
                    )}
                </div>
            </header>

            {error && (
                <p className="invite-error acc-note" role="alert">
                    {error}
                </p>
            )}

            <div className="acc-dev">
                <div className="acc-dev-label">
                    <span>Papel na organização</span>
                    <span className={orgWide ? 'badge pro' : 'badge'}>{orgWide || 'Membro'}</span>
                </div>
                <span className="muted small">
                    {row.kind === 'member'
                        ? `Segurança: ${row.member.security ?? '—'}`
                        : 'Vira acesso quando a pessoa entra com o Google usando este e-mail.'}
                </span>
            </div>

            {units.length > 0 && (
                <div className="acc-tabs" role="tablist" aria-label="Unidades">
                    {units.map((u) => {
                        const v = unitViewOf(row, u.code, teams)
                        return (
                            <button
                                key={u.code}
                                type="button"
                                role="tab"
                                aria-selected={u.code === unit}
                                className={u.code === unit ? 'acc-tab on' : 'acc-tab'}
                                onClick={() => setUnit(u.code)}
                            >
                                <span className={hasUnitAccess(v) ? 'acc-dot on' : 'acc-dot'} aria-hidden />
                                {u.name}
                                {v.role && !orgWide && <span className="acc-tab-role">{v.role}</span>}
                            </button>
                        )
                    })}
                </div>
            )}

            <div className="acc-body" role="tabpanel" aria-label={unitName}>
                {orgWide && (
                    <p className="acc-note muted small">
                        Como {orgWide}, {nameOf(row)} vê e gere todas as unidades.
                    </p>
                )}
                <div className="mem-facts">
                    <div className="acc-panel">
                        <h3 className="acc-panel-title">Cargo</h3>
                        <span className={orgWide || view.role ? undefined : 'muted'}>
                            {orgWide || view.role || `Sem cargo em ${unitName}`}
                        </span>
                    </div>
                    <div className="acc-panel">
                        <h3 className="acc-panel-title">Setores</h3>
                        <span className={view.sectors.length ? undefined : 'muted'}>
                            {view.sectors.join(', ') || 'Nenhum setor'}
                        </span>
                    </div>
                    {row.kind === 'member' && (
                        <div className="acc-panel">
                            <h3 className="acc-panel-title">Exceções · só visualiza</h3>
                            <span className={view.extraGroups || view.extraDashboards ? undefined : 'muted'}>
                                {view.extraGroups || view.extraDashboards
                                    ? `${plural(view.extraGroups, 'grupo extra', 'grupos extras')} · ${plural(view.extraDashboards, 'dashboard avulso', 'dashboards avulsos')}`
                                    : 'Nenhuma'}
                            </span>
                        </div>
                    )}
                </div>

                {row.kind === 'invitation' && (
                    <div className="stack" style={{ gap: 4 }}>
                        <span className="lbl">Link para mandar à pessoa</span>
                        <CopyLink link={inviteLink(window.location.origin)} />
                        {!row.invitation.can_revoke && (
                            <p className="muted small" style={{ margin: 0 }}>
                                Este convite também vale para unidades que você não gere: quem cancela é o Owner ou um
                                Desenvolvedor.
                            </p>
                        )}
                    </div>
                )}
            </div>
        </section>
    )
}
