import { useState, type FormEvent } from 'react'
import { Icon } from '../../components/Icon.tsx'
import { toDataError } from '../../data/errors.ts'
import type { InviteRequest, Team, Unit } from '../../data/types.ts'
import { INVITE_ROLES, invitePreview, validateInvite } from './invite.ts'
import { ROLE_LABEL } from './memberView.ts'

type InvitePanelProps = {
    units: Unit[]
    teams: Team[]
    onSend: (invite: InviteRequest) => Promise<void> // quem usa decide como enviar
    onClose: () => void
}

// Módulo: o formulário "Convidar pessoas". Guarda o que foi digitado e mostra os avisos;
// as regras ficam em invite.ts e o envio fica com quem usa o painel (onSend).
export function InvitePanel({ units, teams, onSend, onClose }: InvitePanelProps) {
    const [emails, setEmails] = useState('')
    const [role, setRole] = useState<InviteRequest['role']>('colaborador')
    const [chosen, setChosen] = useState<string[]>(units[0] ? [units[0].code] : [])
    const [team, setTeam] = useState(teams[0]?.name ?? '')
    const [sending, setSending] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const toggleUnit = (code: string) =>
        setChosen((prev) => (prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]))

    async function submit(e: FormEvent) {
        e.preventDefault() // o formulário não recarrega a página
        const result = validateInvite(emails, chosen)
        if ('error' in result) return setError(result.error)
        setSending(true)
        setError(null)
        try {
            await onSend({ emails: result.emails, role, units: chosen, team })
        } catch (err) {
            setError(toDataError(err).message) // ex.: 409 "Já faz parte da organização"
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
                        {INVITE_ROLES.map((r) => (
                            <option key={r} value={r}>
                                {ROLE_LABEL[r]}
                            </option>
                        ))}
                    </select>
                </label>
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
                <label>
                    <span className="lbl">Equipe</span>
                    <select className="field" value={team} onChange={(e) => setTeam(e.target.value)}>
                        {teams.map((t) => (
                            <option key={t.name} value={t.name}>
                                {t.name}
                            </option>
                        ))}
                    </select>
                </label>
                <div className="invite-preview">
                    {invitePreview(
                        role,
                        chosen,
                        teams.find((t) => t.name === team),
                        units,
                    )}
                </div>
                {error && (
                    <p className="invite-error" role="alert">
                        {error}
                    </p>
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
                    O link vale por 7 dias e fica registrado na auditoria.
                </span>
            </form>
        </aside>
    )
}
