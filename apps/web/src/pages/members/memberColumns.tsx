import type { Column } from '../../components/DataTable.tsx'
import type { Member } from '../../data/types.ts'
import { initialsOf, isWaiting, roleOf, scopeOf, statusOf } from './memberView.ts'

// Módulo: como um membro aparece em cada coluna da tabela (como no protótipo).
export const MEMBER_COLUMNS: Column<Member>[] = [
    {
        header: 'Pessoa',
        render: (m) => (
            <div className="person">
                <span className={isWaiting(m) ? 'av waiting' : 'av'}>{initialsOf(m)}</span>
                <span className="stack" style={{ gap: 0 }}>
                    <span style={{ fontWeight: 500 }}>{m.name ?? m.email}</span>
                    <span className="muted small">{m.note ?? m.email}</span>
                </span>
            </div>
        ),
    },
    { header: 'Papel', render: (m) => <span className={roleOf(m).badge}>{roleOf(m).label}</span> },
    { header: 'Unidades e equipe', render: (m) => <span className="muted">{scopeOf(m)}</span> },
    { header: 'Situação', render: (m) => <span className={statusOf(m).badge}>{statusOf(m).label}</span> },
    { header: 'Segurança', render: (m) => <span className="muted small">{m.security ?? '—'}</span> },
]
