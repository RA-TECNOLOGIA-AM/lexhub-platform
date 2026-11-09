import type { Column } from '../../../components/ui/DataTable.tsx'
import type { PlatformClient } from '../../../types/index.ts'
import { usagePct, usageTone } from '../../admin/billing/billingView.ts'
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
                    <span className="small">
                        {c.seats.used} de {c.seats.total}
                    </span>
                    <div
                        className="usage-track"
                        role="meter"
                        aria-label={`Assentos de ${c.name}`}
                        aria-valuemin={0}
                        aria-valuemax={c.seats.total}
                        aria-valuenow={c.seats.used}
                    >
                        <div
                            className={`usage-fill ${usageTone(c.seats.used, c.seats.total)}`}
                            style={{ width: `${usagePct(c.seats.used, c.seats.total)}%` }}
                        />
                    </div>
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
