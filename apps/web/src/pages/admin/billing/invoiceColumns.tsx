import type { Column } from '../../../components/ui/DataTable.tsx'
import type { Invoice } from '../../../types/index.ts'
import { amountLabel, invoiceStatusOf, monthLabel } from './billingView.ts'

// Módulo: como uma fatura aparece em cada coluna. Parâmetro: o que fazer ao clicar em "Baixar NFS-e".
export function invoiceColumns(onDownload: (invoice: Invoice) => void): Column<Invoice>[] {
    return [
        { header: 'Mês', render: (i) => monthLabel(i.month) },
        { header: 'Valor', render: (i) => amountLabel(i.amount) },
        {
            header: 'Situação',
            render: (i) => <span className={invoiceStatusOf(i.status).badge}>{invoiceStatusOf(i.status).label}</span>,
        },
        {
            header: 'Nota fiscal',
            render: (i) =>
                i.nfse === 'issued' ? (
                    <button className="link-btn" type="button" onClick={() => onDownload(i)}>
                        Baixar NFS-e
                    </button>
                ) : (
                    <span className="muted">NFS-e pendente</span>
                ),
        },
    ]
}
