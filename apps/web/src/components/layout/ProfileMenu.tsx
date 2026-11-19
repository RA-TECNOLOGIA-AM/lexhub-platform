import { useRef, useState, type ChangeEvent } from 'react'
import { useAuth } from '../../contexts/auth-context.ts'
import { useDismiss } from '../../hooks/useDismiss.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { AVATAR_ACCEPT, avatarFileError, toAvatarBlob } from '../../lib/avatarImage.ts'
import { dataClient } from '../../services/client.ts'
import { DataError, toDataError } from '../../services/errors.ts'
import type { User } from '../../types/index.ts'
import { Avatar } from '../ui/Avatar.tsx'

type ProfileMenuProps = {
    user: User // quem está logado (do /me): nome, iniciais, foto, cargo, setores e escritórios
}

// Módulo: o avatar no canto direito da topbar e o cartão de perfil que ele abre (mesmo popover do Período).
// O e-mail vem da sessão (é o do login); o resto vem do /me. Só a foto é editável aqui.
export function ProfileMenu({ user }: ProfileMenuProps) {
    const { setAvatarPath } = useAuth()
    const [open, setOpen] = useState(false)
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const root = useRef<HTMLDivElement>(null)
    const button = useRef<HTMLButtonElement>(null)
    const fileInput = useRef<HTMLInputElement>(null)
    const email = useAsync(() => dataClient.getSessionEmail(), [])

    useDismiss({
        open,
        onClose: () => setOpen(false),
        isInside: (target) => !!root.current?.contains(target),
        returnFocus: button,
    })

    function toggle() {
        setError(null)
        setOpen((o) => !o)
    }

    // Faz a troca (ou a remoção) e mostra o erro no cartão, sem fechar.
    async function run(action: () => Promise<string | null>) {
        setBusy(true)
        setError(null)
        try {
            setAvatarPath(await action())
        } catch (err) {
            setError(toDataError(err).message)
        } finally {
            setBusy(false)
        }
    }

    function onPick(e: ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0]
        e.target.value = '' // escolher a mesma foto de novo também dispara
        if (!file) return
        const invalid = avatarFileError(file)
        if (invalid) {
            setError(invalid)
            return
        }
        void run(async () => {
            const image = await toAvatarBlob(file).catch(() => {
                throw new DataError(0, 'Não foi possível ler esta foto.')
            })
            return dataClient.uploadMyAvatar(image)
        })
    }

    const rows = [
        { label: 'Cargo', value: user.role_label },
        { label: 'Setor', value: user.teams.join(', ') },
        { label: 'Escritório', value: user.offices.join(', ') },
    ]

    return (
        <div className="popover-wrap" ref={root}>
            <button
                ref={button}
                className="profile-btn"
                type="button"
                aria-label={`Perfil de ${user.name}`}
                title={user.name}
                aria-expanded={open}
                aria-haspopup="dialog"
                onClick={toggle}
            >
                <Avatar user={user} className="profile-face" />
            </button>
            {open && (
                <div className="card popover profile-popover" role="dialog" aria-label="Meu perfil">
                    <div className="profile-head">
                        <button
                            className="profile-btn profile-av"
                            type="button"
                            title="Trocar foto"
                            aria-label="Trocar foto"
                            disabled={busy}
                            onClick={() => fileInput.current?.click()}
                        >
                            <Avatar user={user} className="profile-face" />
                        </button>
                        <span className="profile-id">
                            <strong className="profile-name">{user.name}</strong>
                            {email.data && <span className="small muted profile-email">{email.data}</span>}
                            <span className="profile-photo-actions">
                                <button
                                    className="linkbtn small"
                                    type="button"
                                    disabled={busy}
                                    onClick={() => fileInput.current?.click()}
                                >
                                    {busy ? 'Salvando…' : 'Trocar foto'}
                                </button>
                                {user.avatar_path && !busy && (
                                    <button
                                        className="linkbtn small"
                                        type="button"
                                        onClick={() =>
                                            void run(async () => {
                                                await dataClient.removeMyAvatar()
                                                return null
                                            })
                                        }
                                    >
                                        Remover
                                    </button>
                                )}
                            </span>
                        </span>
                        <input ref={fileInput} type="file" accept={AVATAR_ACCEPT} hidden onChange={onPick} />
                    </div>
                    {error && (
                        <p className="small profile-error" role="alert">
                            {error}
                        </p>
                    )}
                    <dl className="profile-rows">
                        {rows.map((row) => (
                            <div key={row.label} className="profile-row">
                                <dt>{row.label}</dt>
                                <dd>{row.value || '—'}</dd>
                            </div>
                        ))}
                    </dl>
                </div>
            )}
        </div>
    )
}
