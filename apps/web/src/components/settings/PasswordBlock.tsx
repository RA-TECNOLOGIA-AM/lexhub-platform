import { useEffect, useState } from 'react'
import { useAsync } from '../../hooks/useAsync.ts'
import { dataClient } from '../../services/client.ts'
import { toDataError } from '../../services/errors.ts'
import { PasswordInput } from '../ui/PasswordInput.tsx'

// Módulo: Configurações → Perfil → Senha. Quem só entra pelo Google cria a senha; quem já tem, troca.
// A senha atual não é pedida (a sessão já está aberta); a troca vai para a auditoria por um trigger no banco.

const MIN_LENGTH = 6

// null = pode salvar; senão, a mensagem para a pessoa.
export function validatePassword(password: string, confirm: string): string | null {
    if (!password.trim() || !confirm.trim()) return 'Preencha os dois campos.'
    if (password !== confirm) return 'As senhas não coincidem.'
    if (password.length < MIN_LENGTH) return `A senha precisa ter pelo menos ${MIN_LENGTH} caracteres.`
    return null
}

export type PasswordBlockViewProps = {
    hasPassword: boolean | null // null = carregando
    editing: boolean
    password: string
    confirm: string
    busy: boolean
    error: string | null
    saved: boolean
    onEdit: () => void
    onCancel: () => void
    onSave: () => void
    onPassword: (value: string) => void
    onConfirm: (value: string) => void
}

export function PasswordBlockView(p: PasswordBlockViewProps) {
    const value = p.hasPassword === null ? '—' : p.hasPassword ? '••••••••' : 'Não definida'
    return (
        <div className="settings-fields settings-fields-split">
            <div className="settings-field">
                <div className="settings-field-head">
                    <span className="settings-field-label">Senha</span>
                    {!p.editing && p.hasPassword !== null && (
                        <button className="btn btn-sm btn-ghost" type="button" onClick={p.onEdit}>
                            {p.hasPassword ? 'Alterar senha' : 'Criar senha'}
                        </button>
                    )}
                </div>

                {!p.editing && (
                    <p className={p.hasPassword ? 'settings-field-value' : 'settings-field-value muted'}>{value}</p>
                )}
                {!p.editing && !p.hasPassword && p.hasPassword !== null && (
                    <p className="small muted">Com uma senha, você entra também com e-mail e senha, além do Google.</p>
                )}
                {p.saved && !p.editing && (
                    <p className="small settings-ok" role="status">
                        Senha salva. Você já pode entrar com e-mail e senha.
                    </p>
                )}

                {p.editing && (
                    <form
                        className="settings-password-form"
                        onSubmit={(e) => {
                            e.preventDefault()
                            p.onSave()
                        }}
                        noValidate
                    >
                        <label className="lbl" htmlFor="nova-senha">
                            Nova senha
                        </label>
                        <PasswordInput
                            id="nova-senha"
                            value={p.password}
                            onChange={p.onPassword}
                            autoComplete="new-password"
                        />
                        <label className="lbl" htmlFor="confirmar-senha">
                            Confirmar nova senha
                        </label>
                        <PasswordInput
                            id="confirmar-senha"
                            value={p.confirm}
                            onChange={p.onConfirm}
                            autoComplete="new-password"
                        />
                        {p.error && (
                            <p className="small profile-error" role="alert">
                                {p.error}
                            </p>
                        )}
                        <div className="settings-password-actions">
                            <button
                                className="btn btn-sm btn-ghost"
                                type="button"
                                onClick={p.onCancel}
                                disabled={p.busy}
                            >
                                Cancelar
                            </button>
                            <button className="btn btn-sm btn-primary" type="submit" disabled={p.busy}>
                                {p.busy ? 'Salvando…' : 'Salvar'}
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    )
}

export function PasswordBlock() {
    const status = useAsync(() => dataClient.getPasswordStatus(), [])
    const [hasPassword, setHasPassword] = useState<boolean | null>(null)
    const [editing, setEditing] = useState(false)
    const [password, setPassword] = useState('')
    const [confirm, setConfirm] = useState('')
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [saved, setSaved] = useState(false)

    // Sem resposta do banco (erro), trata como sem senha: o botão "Criar senha" também troca.
    useEffect(() => {
        if (status.data !== undefined && status.data !== null) setHasPassword(status.data)
        else if (status.error) setHasPassword(false)
    }, [status.data, status.error])

    const close = () => {
        setEditing(false)
        setPassword('')
        setConfirm('')
        setError(null)
    }

    async function save() {
        const invalid = validatePassword(password, confirm)
        if (invalid) return setError(invalid)
        setBusy(true)
        setError(null)
        try {
            await dataClient.setPassword(password)
            setHasPassword(true)
            setSaved(true)
            close()
        } catch (err) {
            setError(toDataError(err).message)
        } finally {
            setBusy(false)
        }
    }

    return (
        <PasswordBlockView
            hasPassword={hasPassword}
            editing={editing}
            password={password}
            confirm={confirm}
            busy={busy}
            error={error}
            saved={saved}
            onEdit={() => {
                setSaved(false)
                setEditing(true)
            }}
            onCancel={close}
            onSave={save}
            onPassword={setPassword}
            onConfirm={setConfirm}
        />
    )
}
