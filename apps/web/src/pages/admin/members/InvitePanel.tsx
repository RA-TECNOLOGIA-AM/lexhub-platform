import { useState, type FormEvent } from 'react'
import { Icon } from '../../../components/ui/Icon.tsx'
import { toDataError } from '../../../services/errors.ts'
import type { InviteRequest, InviteResult, MemberTeam, Unit } from '../../../types/index.ts'
import { CopyLink } from './CopyLink.tsx'
import { inviteLink, inviteRolesFor, teamsFor, validateInvite } from './invite.ts'
import { ROLE_LABEL } from './memberView.ts'

type InvitePanelProps = {
    units: Unit[] // as unidades que quem convida gere
    teams: MemberTeam[]
    canInviteAdmin: boolean
    onSend: (invite: InviteRequest) => Promise<InviteResult> // quem usa decide como enviar
    onClose: () => void
}

const toggle = (list: string[], value: string) =>
    list.includes(value) ? list.filter((v) => v !== value) : [...list, value]

// Módulo: o formulário "Convidar pessoas". Guarda o que foi digitado, mostra os avisos e,
// depois de enviar, o resultado e o link para mandar à pessoa (não sai e-mail automático).
// As regras ficam em invite.ts; o envio fica com quem usa o painel (onSend).
export function InvitePanel({ units, teams, canInviteAdmin, onSend, onClose }: InvitePanelProps) {
    const [emails, setEmails] = useState('')
    const [role, setRole] = useState<InviteRequest['role']>('colaborador')
    const [chosen, setChosen] = useState<string[]>(units.length === 1 ? [units[0].code] : [])
    const [chosenTeams, setChosenTeams] = useState<string[]>([])
    const [sending, setSending] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [result, setResult] = useState<InviteResult | null>(null)

    const isAdmin = role === 'admin'
    const visibleTeams = isAdmin ? [] : teamsFor(teams, chosen)

    function toggleUnit(code: string) {
        const next = toggle(chosen, code)
        setChosen(next)
        // Equipe de unidade que saiu da escolha também sai.
        setChosenTeams((prev) => prev.filter((id) => teamsFor(teams, next).some((t) => t.id === id)))
    }

    async function submit(e: FormEvent) {
        e.preventDefault() // o formulário não recarrega a página
        const valid = validateInvite(emails, role, chosen)
        if ('error' in valid) return setError(valid.error)
        setSending(true)
        setError(null)
        try {
            const sent = await onSend({
                emails: valid.emails,
                role,
                units: isAdmin ? [] : chosen,
                teams: isAdmin ? [] : chosenTeams,
            })
            setResult(sent)
            if (sent.invited.length) setEmails('')
        } catch (err) {
            setError(toDataError(err).message)
        } finally {
            setSending(false)
        }
    }

    return (
        <aside className="card invite" aria-label="Convidar pessoas">
            <form className="stack" style={{ gap: 14 }} onSubmit={submit}>
                <div className="invite-head">
                    <h2 className="h2">Convidar pessoas</h2>
                    <button className="iconbtn" type="button" aria-label="Fechar" onClick={onClose}>
                        <Icon name="close" size={16} />
                    </button>
                </div>
                <label>
                    <span className="lbl">E-mails</span>
                    <textarea
                        className="field"
                        rows={3}
                        placeholder="fernanda@lexgroup.com.br, gabriel@lexgroup.com.br"
                        value={emails}
                        onChange={(e) => setEmails(e.target.value)}
                    />
                </label>
                <label>
                    <span className="lbl">Papel</span>
                    <select
                        className="field"
                        value={role}
                        onChange={(e) => setRole(e.target.value as InviteRequest['role'])}
                    >
                        {inviteRolesFor(canInviteAdmin).map((r) => (
                            <option key={r} value={r}>
                                {ROLE_LABEL[r]}
                            </option>
                        ))}
                    </select>
                </label>
                {isAdmin ? (
                    <div className="invite-preview">Desenvolvedor vale em todas as unidades da organização.</div>
                ) : (
                    <>
                        <fieldset className="invite-units">
                            <legend className="lbl">Unidades</legend>
                            {units.map((u) => (
                                <label key={u.code} className="check">
                                    <input
                                        type="checkbox"
                                        checked={chosen.includes(u.code)}
                                        onChange={() => toggleUnit(u.code)}
                                    />
                                    {u.name}
                                </label>
                            ))}
                        </fieldset>
                        <fieldset className="invite-units">
                            <legend className="lbl">Equipes</legend>
                            {visibleTeams.length === 0 && (
                                <span className="muted small">
                                    {chosen.length
                                        ? 'Nenhuma equipe nessas unidades.'
                                        : 'Escolha uma unidade primeiro.'}
                                </span>
                            )}
                            {visibleTeams.map((t) => (
                                <label key={t.id} className="check">
                                    <input
                                        type="checkbox"
                                        checked={chosenTeams.includes(t.id)}
                                        onChange={() => setChosenTeams((prev) => toggle(prev, t.id))}
                                    />
                                    {t.name}
                                    <span className="muted small">· {t.unit.replace('_', ' ')}</span>
                                </label>
                            ))}
                        </fieldset>
                    </>
                )}
                {error && (
                    <p className="invite-error" role="alert">
                        {error}
                    </p>
                )}
                {result && (
                    <div className="invite-preview stack" style={{ gap: 6 }} role="status">
                        {result.invited.length > 0 && <span>Convidados: {result.invited.join(', ')}</span>}
                        {result.skipped.map((s) => (
                            <span key={s.email}>
                                {s.email}: {s.reason}
                            </span>
                        ))}
                        {result.invited.length > 0 && (
                            <>
                                <span>
                                    Peça para a pessoa entrar com o Google usando este e-mail. O convite vale por 7
                                    dias.
                                </span>
                                <CopyLink link={inviteLink(window.location.origin)} />
                            </>
                        )}
                    </div>
                )}
                <button
                    className="btn btn-primary"
                    type="submit"
                    disabled={sending}
                    style={{ justifyContent: 'center' }}
                >
                    {sending ? 'Enviando…' : 'Enviar convites'}
                </button>
                <span className="muted small" style={{ textAlign: 'center' }}>
                    Não sai e-mail: mande o link para a pessoa. Tudo fica registrado na auditoria.
                </span>
            </form>
        </aside>
    )
}
