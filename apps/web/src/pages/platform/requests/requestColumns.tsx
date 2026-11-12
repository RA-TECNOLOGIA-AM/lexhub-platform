import type { Column } from '../../../components/ui/DataTable.tsx'
import type { AccessRequest } from '../../../types/index.ts'
import { requestDate } from '../../login/noAccessView.ts'

const STATUS = {
    pending: { label: 'Pendente', badge: 'badge warn' },
    approved: { label: 'Aprovado', badge: 'badge ok' },
    rejected: { label: 'Recusado', badge: 'badge danger' },
} as const

// Módulo: como um pedido aparece em cada coluna. Parâmetros: o que fazer em Aprovar e Recusar
// (sem eles, a tabela é só leitura: aba Decididos).
export function requestColumns(actions?: {
    onApprove: (r: AccessRequest) => void
    onReject: (r: AccessRequest) => void
}): Column<AccessRequest>[] {
    const columns: Column<AccessRequest>[] = [
        {
            header: 'Pessoa',
            render: (r) => (
                <span className="stack" style={{ gap: 0 }}>
                    <span style={{ fontWeight: 500 }}>{r.full_name}</span>
                    <span className="muted small">{r.email}</span>
                </span>
            ),
        },
        { header: 'Escritório', render: (r) => r.office },
        { header: 'Mensagem', render: (r) => <span className="small">{r.message ?? '—'}</span> },
        { header: 'Pedido em', render: (r) => requestDate(r.created_at) },
    ]
    if (!actions) {
        columns.push({
            header: 'Decisão',
            render: (r) => (
                <span className="stack" style={{ gap: 2 }}>
                    <span className={STATUS[r.status].badge}>{STATUS[r.status].label}</span>
                    {r.decided_at && <span className="muted small">{requestDate(r.decided_at)}</span>}
                    {r.decision_note && <span className="muted small">{r.decision_note}</span>}
                </span>
            ),
        })
        return columns
    }
    columns.push({
        header: 'Ações',
        align: 'right',
        render: (r) => (
            <span className="row" style={{ justifyContent: 'flex-end', gap: 8 }}>
                <button className="btn" type="button" onClick={() => actions.onReject(r)}>
                    Recusar
                </button>
                <button className="btn btn-primary" type="button" onClick={() => actions.onApprove(r)}>
                    Aprovar
                </button>
            </span>
        ),
    })
    return columns
}
