import { Link } from 'react-router'
import type { Column } from '../../../components/ui/DataTable.tsx'
import type { PlatformClient } from '../../../types/index.ts'
import { usageText } from '../../admin/billing/billingView.ts'
import { UsageMeter } from '../../admin/billing/UsageMeter.tsx'
import { billingOf, dataOf, planOf } from './clientsView.ts'

const badge = (b: { label: string; badge: string }) => <span className={b.badge}>{b.label}</span>

type ClientActions = {
    onSupport: (client: PlatformClient) => void // "Entrar como suporte"
    onCloseOrg: (client: PlatformClient) => void // "Encerrar" (só aparece em quem pode ser encerrada)
}

// Módulo: como um cliente aparece em cada coluna. Parâmetro: o que fazer em cada ação da linha.
// As unidades da organização ficam embaixo do nome; cada uma abre Unidades e fontes com ela selecionada.
export function clientColumns({ onSupport, onCloseOrg }: ClientActions): Column<PlatformClient>[] {
    return [
        {
            header: 'Organização',
            render: (c) => (
                <span className="stack" style={{ gap: 0 }}>
                    <span style={{ fontWeight: 500 }}>{c.name}</span>
                    <span className="muted small">{c.sub}</span>
                    {c.units.length > 0 && (
                        <span className="client-units">
                            {c.units.map((u) => (
                                <Link
                                    key={u.code}
                                    className="client-unit"
                                    to={`/plataforma/clientes/${c.slug}/unidades?unidade=${encodeURIComponent(u.code)}`}
                                    title={`Abrir ${u.name} em Unidades e fontes`}
                                >
                                    {u.name}
                                </Link>
                            ))}
                        </span>
                    )}
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
                <span className="row" style={{ gap: 6, flexWrap: 'nowrap' }}>
                    <button className="btn nowrap" type="button" onClick={() => onSupport(c)}>
                        Entrar como suporte
                    </button>
                    {c.canClose && (
                        <button className="btn btn-danger nowrap" type="button" onClick={() => onCloseOrg(c)}>
                            Encerrar
                        </button>
                    )}
                </span>
            ),
        },
    ]
}
