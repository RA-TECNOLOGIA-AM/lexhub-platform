import { useState } from 'react'
import { Link } from 'react-router'
import { Icon } from '../../../components/ui/Icon.tsx'
import { toDataError } from '../../../services/errors.ts'
import { CopyLink } from './CopyLink.tsx'
import { inviteLink } from './invite.ts'
import { nameOf, noteOf, ROLE_LABEL, scopeOf, statusOf, type MemberRow } from './memberView.ts'

type MemberPanelProps = {
    row: MemberRow
    isSelf: boolean // a própria pessoa não se desativa
    accessHref: string // onde se editam cargos e equipes (aba Acesso)
    onSetStatus: (status: 'active' | 'disabled') => Promise<void>
    onRevoke: () => Promise<void>
    onClose: () => void
}

// Módulo: o painel de uma pessoa (ou de um convite) ao lado da lista.
// Mostra cargos e equipes só para leitura; muda a situação ou cancela o convite pelo que recebe.
export function MemberPanel({ row, isSelf, accessHref, onSetStatus, onRevoke, onClose }: MemberPanelProps) {
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

    return (
        <aside className="card invite stack" style={{ gap: 14 }} aria-label={`Detalhes de ${nameOf(row)}`}>
            <div className="invite-head">
                <h2 className="h2">{nameOf(row)}</h2>
                <button className="iconbtn" type="button" aria-label="Fechar" onClick={onClose}>
                    <Icon name="close" size={16} />
                </button>
            </div>
            <span className="muted small">{noteOf(row, now)}</span>
            <span>
                <span className={statusOf(row).badge}>{statusOf(row).label}</span>
            </span>

            {row.kind === 'member' ? (
                <>
                    <div className="stack" style={{ gap: 4 }}>
                        <span className="lbl">Cargos</span>
                        {row.member.org_role !== 'member' && (
                            <span>{ROLE_LABEL[row.member.org_role]} · todas as unidades</span>
                        )}
                        {row.member.units.map((u) => (
                            <span key={u.code}>
                                {u.code.replace('_', ' ')}: {ROLE_LABEL[u.role]}
                            </span>
                        ))}
                        {row.member.org_role === 'member' && row.member.units.length === 0 && (
                            <span className="muted">Sem cargo nas suas unidades</span>
                        )}
                    </div>
                    <div className="stack" style={{ gap: 4 }}>
                        <span className="lbl">Equipes</span>
                        <span className={row.member.teams.length ? undefined : 'muted'}>
                            {row.member.teams.join(', ') || 'Sem equipe'}
                        </span>
                    </div>
                    <Link className="linkbtn" to={accessHref}>
                        Editar cargos e equipes em Acesso
                    </Link>
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
                </>
            ) : (
                <>
                    <div className="stack" style={{ gap: 4 }}>
                        <span className="lbl">Convite</span>
                        <span>{ROLE_LABEL[row.invitation.role]}</span>
                        <span className="muted">{scopeOf(row)}</span>
                    </div>
                    <div className="stack" style={{ gap: 4 }}>
                        <span className="lbl">Link para mandar à pessoa</span>
                        <CopyLink link={inviteLink(window.location.origin)} />
                    </div>
                    {row.invitation.can_revoke ? (
                        <button
                            className="btn"
                            type="button"
                            disabled={busy}
                            onClick={() => run(`Cancelar o convite de ${row.invitation.email}?`, onRevoke)}
                        >
                            Cancelar convite
                        </button>
                    ) : (
                        <p className="muted small" style={{ margin: 0 }}>
                            Este convite também vale para unidades que você não gere: quem cancela é o Owner ou um
                            Desenvolvedor.
                        </p>
                    )}
                </>
            )}

            {error && (
                <p className="invite-error" role="alert">
                    {error}
                </p>
            )}
        </aside>
    )
}
