import type { Column } from '../../../components/ui/DataTable.tsx'
import type { AuditEvent } from '../../../types/index.ts'
import { KIND, whenLabel } from './auditView.ts'

// Módulo: como um evento aparece em cada coluna da tabela (como no protótipo).
export const AUDIT_COLUMNS: Column<AuditEvent>[] = [
    {
        header: 'Quando',
        render: (e) => (
            <time className="muted small nowrap" dateTime={e.at}>
                {whenLabel(e.at)}
            </time>
        ),
    },
    { header: 'Quem', render: (e) => <span className="nowrap">{e.actor}</span> },
    { header: 'O que aconteceu', render: (e) => <span className={KIND[e.kind].badge}>{e.action}</span> },
    { header: 'Detalhe', render: (e) => <span className="muted small">{e.detail}</span> },
]
