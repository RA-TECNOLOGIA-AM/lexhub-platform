import { useAuth } from '../../contexts/auth-context.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { useAvatarUpload } from '../../hooks/useAvatarUpload.ts'
import { dataClient } from '../../services/client.ts'
import { Avatar } from '../ui/Avatar.tsx'
import { Icon } from '../ui/Icon.tsx'
import { AvatarCropDialog } from './AvatarCropDialog.tsx'

// Módulo: Configurações → Perfil. Mostra quem está logado; só a foto é editável aqui.
// Nome, cargo, setor e escritório são do administrador (Membros/Acesso); o e-mail é o do login.
export function ProfileSection() {
    const { me } = useAuth()
    const email = useAsync(() => dataClient.getSessionEmail(), [])
    const photo = useAvatarUpload()
    if (!me) return null
    const user = me.user

    const rows = [
        { label: 'Nome de exibição', value: user.name },
        { label: 'E-mail', value: email.data },
    ]
    const work = [
        { label: 'Cargo', value: user.role_label },
        { label: 'Setor', value: user.teams.join(', ') },
        { label: 'Escritório', value: user.offices.join(', ') },
    ]

    return (
        <div className="settings-stack">
            <div className="settings-card settings-profile">
                <span className="settings-avatar">
                    <Avatar user={user} className="settings-avatar-face" />
                    <button
                        className="settings-avatar-cam"
                        type="button"
                        aria-label="Trocar foto"
                        title="Trocar foto"
                        disabled={photo.busy}
                        onClick={photo.choose}
                    >
                        <Icon name="camera" size={15} />
                    </button>
                    <input {...photo.input} />
                    {photo.crop && <AvatarCropDialog {...photo.crop} />}
                </span>
                <span className="settings-profile-id">
                    <strong className="settings-profile-name">{user.name}</strong>
                    {email.data && <span className="muted">{email.data}</span>}
                    {photo.busy && <span className="small muted">Salvando a foto…</span>}
                    {user.avatar_path && !photo.busy && (
                        <button className="linkbtn small" type="button" onClick={photo.remove}>
                            Remover foto
                        </button>
                    )}
                </span>
            </div>
            {photo.error && (
                <p className="small profile-error" role="alert">
                    {photo.error}
                </p>
            )}

            <dl className="settings-fields">
                {rows.map((row) => (
                    <div key={row.label} className="settings-field">
                        <dt>{row.label}</dt>
                        <dd>{row.value || '—'}</dd>
                    </div>
                ))}
            </dl>
            <dl className="settings-fields settings-fields-split">
                {work.map((row) => (
                    <div key={row.label} className="settings-field">
                        <dt>{row.label}</dt>
                        <dd>{row.value || '—'}</dd>
                    </div>
                ))}
            </dl>
            <p className="small muted">
                Nome, cargo, setor e escritório são definidos pela administração da sua organização.
            </p>
        </div>
    )
}
