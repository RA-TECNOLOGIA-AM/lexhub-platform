import { useRef, useState } from 'react'
import { useDismiss } from '../../hooks/useDismiss.ts'
import { useAsync } from '../../hooks/useAsync.ts'
import { dataClient } from '../../services/client.ts'
import type { User } from '../../types/index.ts'
import { Avatar } from '../ui/Avatar.tsx'

type ProfileMenuProps = {
    user: User // quem está logado (do /me): nome, iniciais, foto, cargo, setores e escritórios
}

// Módulo: o avatar no canto direito da topbar e o cartão de perfil que ele abre (mesmo popover do Período).
// Só leitura: o e-mail vem da sessão (é o do login); o resto vem do /me. A foto se troca em
// Configurações → Perfil (engrenagem da topbar).
export function ProfileMenu({ user }: ProfileMenuProps) {
    const [open, setOpen] = useState(false)
    const root = useRef<HTMLDivElement>(null)
    const button = useRef<HTMLButtonElement>(null)
    const email = useAsync(() => dataClient.getSessionEmail(), [])

    useDismiss({
        open,
        onClose: () => setOpen(false),
        isInside: (target) => !!root.current?.contains(target),
        returnFocus: button,
    })

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
                onClick={() => setOpen((o) => !o)}
            >
                <Avatar user={user} className="profile-face" />
            </button>
            {open && (
                <div className="card popover profile-popover" role="dialog" aria-label="Meu perfil">
                    <div className="profile-head">
                        <span className="profile-btn profile-av">
                            <Avatar user={user} className="profile-face" />
                        </span>
                        <span className="profile-id">
                            <strong className="profile-name">{user.name}</strong>
                            {email.data && <span className="small muted profile-email">{email.data}</span>}
                        </span>
                    </div>
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
