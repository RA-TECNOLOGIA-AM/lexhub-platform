import type { Column } from '../../../components/ui/DataTable.tsx'
import type { PlatformClient } from '../../../types/index.ts'
import { usageText } from '../../admin/billing/billingView.ts'
import { UsageMeter } from '../../admin/billing/UsageMeter.tsx'
import { billingOf, dataOf, planOf } from './clientsView.ts'

const badge = (b: { label: string; badge: string }) => <span className={b.badge}>{b.label}</span>

// Módulo: como um cliente aparece em cada coluna. Parâmetro: o que fazer em "Entrar como suporte".
export function clientColumns(onSupport: (client: PlatformClient) => void): Column<PlatformClient>[] {
    return [
        {
            header: 'Organização',
            render: (c) => (
                <span className="stack" style={{ gap: 0 }}>
                    <span style={{ fontWeight: 500 }}>{c.name}</span>
                    <span className="muted small">{c.sub}</span>
                </span>
            ),
        },
        { header: 'Plano', render: (c) => badge(planOf(c)) },
        {
            header: 'Assentos',
            render: (c) => (
                <div className="seats">
                    <span className="small">{usageText(c.seats.used, c.seats.total)}</span>
                    <UsageMeter label={`Assentos de ${c.name}`} used={c.seats.used} total={c.seats.total} />
                </div>
            ),
        },
        { header: 'Dados', render: (c) => badge(dataOf(c)) },
        { header: 'Cobrança', render: (c) => badge(billingOf(c)) },
        {
            header: 'Ações',
            render: (c) => (
                <button className="btn nowrap" type="button" onClick={() => onSupport(c)}>
                    Entrar como suporte
                </button>
            ),
        },
    ]
}
