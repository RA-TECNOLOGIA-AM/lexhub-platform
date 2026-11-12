import type { Column } from '../../../components/ui/DataTable.tsx'
import { initialsOf, nameOf, noteOf, roleOf, scopeOf, statusOf, type MemberRow } from './memberView.ts'

// Módulo: como cada linha (membro ou convite) aparece em cada coluna, como no protótipo.
// Parâmetros: a unidade escolhida no seletor (null = todas), o "agora" (para "vence em N dias")
// e o que fazer ao clicar na pessoa (abrir o painel).
export function memberColumns(unit: string | null, now: Date, onOpen: (row: MemberRow) => void): Column<MemberRow>[] {
    return [
        {
            header: 'Pessoa',
            render: (row) => (
                <div className="person">
                    <span className={row.kind === 'invitation' ? 'av waiting' : 'av'}>{initialsOf(row)}</span>
                    <span className="stack" style={{ gap: 0 }}>
                        <button
                            className="linkbtn"
                            type="button"
                            style={{ color: 'inherit', textAlign: 'left' }}
                            onClick={() => onOpen(row)}
                        >
                            {nameOf(row)}
                        </button>
                        <span className="muted small">{noteOf(row, now)}</span>
                    </span>
                </div>
            ),
        },
        {
            header: 'Papel',
            render: (row) => <span className={roleOf(row, unit).badge}>{roleOf(row, unit).label}</span>,
        },
        { header: 'Unidades e equipes', render: (row) => <span className="muted">{scopeOf(row)}</span> },
        { header: 'Situação', render: (row) => <span className={statusOf(row).badge}>{statusOf(row).label}</span> },
        {
            header: 'Segurança',
            render: (row) => (
                <span className="muted small">{(row.kind === 'member' && row.member.security) || '—'}</span>
            ),
        },
    ]
}
