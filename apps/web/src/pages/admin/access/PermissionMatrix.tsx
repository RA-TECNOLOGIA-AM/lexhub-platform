import { Icon } from '../../../components/ui/Icon.tsx'
import type { AccessCell, Permission } from '../../../types/index.ts'
import { ROLE_LABEL } from '../members/memberView.ts'
import { ROLE_ORDER } from './accessView.ts'

// Uma célula: ✓ (sim), — (não) ou o selo com a ressalva.
function Cell({ cell }: { cell: AccessCell }) {
    if (cell.kind === 'yes') {
        return (
            <span className="cell-yes" role="img" aria-label="Sim">
                <Icon name="check" size={18} />
            </span>
        )
    }
    if (cell.kind === 'no') {
        return (
            <span className="cell-no" aria-label="Não">
                —
            </span>
        )
    }
    return <span className="badge neutral">{cell.note}</span>
}

// Módulo: a matriz "Papéis". Uma linha por permissão, uma coluna por papel.
export function PermissionMatrix({ matrix }: { matrix: Permission[] }) {
    return (
        <section className="card" style={{ overflow: 'hidden' }} aria-label="Papéis">
            <div className="card-head" style={{ paddingBottom: 12 }}>
                <h2 className="h2">Papéis</h2>
            </div>
            <div className="tblwrap">
                <table className="tbl" style={{ minWidth: 640 }}>
                    <thead>
                        <tr>
                            <th>Permissão</th>
                            {ROLE_ORDER.map((r) => (
                                <th key={r} className="center">
                                    {ROLE_LABEL[r]}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {matrix.map((p) => (
                            <tr key={p.key}>
                                <td>{p.label}</td>
                                {ROLE_ORDER.map((r) => (
                                    <td key={r} className="center">
                                        <Cell cell={p.cells[r]} />
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </section>
    )
}
