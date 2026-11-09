import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import type { ClientKpis as Kpis } from './clientsView.ts'

// Módulo: os 4 indicadores do topo da página Clientes.
export function ClientKpis({ kpis }: { kpis: Kpis }) {
    return (
        <div className="grid grid-kpi">
            <Kpi label="Organizações ativas" value={kpis.active} />
            <Kpi label="Em implantação" value={kpis.onboarding} />
            <Kpi label="Receita mensal" value={kpis.revenue} />
            <Kpi
                label="Fontes com falha"
                value={kpis.failingSources}
                tone={kpis.failingSources > 0 ? 'warn' : undefined}
            />
        </div>
    )
}
