import { Avatar } from '../../../components/ui/Avatar.tsx'
import { initialsOf, isOnline, nameOf, type MemberRow } from './memberView.ts'

type MemberAvatarProps = {
    row: MemberRow
    now: Date
    className?: string // classe do círculo: 'mem-av' na lista, 'acc-av' no detalhe
}

// Módulo: o círculo da pessoa em Membros — foto de perfil (ou iniciais) e, se ela estiver online,
// uma bolinha verde no canto. Convite: iniciais do e-mail em amarelo, sem bolinha.
export function MemberAvatar({ row, now, className = 'mem-av' }: MemberAvatarProps) {
    if (row.kind === 'invitation') return <span className={`av ${className} waiting`}>{initialsOf(row)}</span>
    const online = isOnline(row, now)
    return (
        <span className="mem-av-wrap">
            <Avatar
                user={{ name: nameOf(row), initials: initialsOf(row), avatar_path: row.member.avatar_path ?? null }}
                className={`av ${className}`}
            />
            {online && <span className="mem-online-dot" role="img" aria-label="Online agora" />}
        </span>
    )
}
