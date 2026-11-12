import { Icon } from '../../../components/ui/Icon.tsx'
import type { AccessOverview } from '../../../types/index.ts'
import { ROLE_LABEL } from '../members/memberView.ts'
import { gridCell, type GridCell } from './accessEditor.ts'

function Cell({ cell }: { cell: GridCell }) {
    if (cell.kind === 'all') {
        return (
            <span className="cell-yes" role="img" aria-label="Vê">
                <Icon name="check" size={18} />
            </span>
        )
    }
    if (cell.kind === 'none') {
        return (
            <span className="cell-no" aria-label="Nenhuma equipe libera">
                —
            </span>
        )
    }
    return (
        <span className="pills" style={{ gap: 4, justifyContent: 'center' }}>
            {cell.teams.map((t) => (
                <span key={t} className="tag">
                    {t}
                </span>
            ))}
        </span>
    )
}

// Módulo: a grade "O que cada cargo vê" de uma unidade. Linhas = dashboards ligados na unidade;
// colunas = cargos. Gestor/Controller veem tudo; Colaborador/Leitor, o que as equipes liberam.
export function RoleGrid({ overview }: { overview: AccessOverview }) {
    const unitName = overview.units.find((u) => u.code === overview.unit)?.name ?? overview.unit
    return (
        <section className="card" style={{ overflow: 'hidden' }} aria-label="O que cada cargo vê">
            <div className="card-head" style={{ paddingBottom: 4 }}>
                <h2 className="h2">O que cada cargo vê em {unitName}</h2>
            </div>
            <p className="muted small" style={{ margin: '0 18px 12px' }}>
                Owner e Desenvolvedor veem todos os dashboards de todas as unidades. Colaborador e Leitor veem o que as
                equipes deles liberam.
            </p>
            {overview.dashboards.length === 0 ? (
                <p className="muted" style={{ margin: '0 18px 18px' }}>
                    Nenhum dashboard ligado nesta unidade.
                </p>
            ) : (
                <div className="tblwrap">
                    <table className="tbl" style={{ minWidth: 640 }}>
                        <thead>
                            <tr>
                                <th>Dashboard</th>
                                {overview.roles.map((r) => (
                                    <th key={r.key} className="center">
                                        {ROLE_LABEL[r.key]}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {overview.dashboards.map((d) => (
                                <tr key={d.key}>
                                    <td>
                                        <span style={{ fontWeight: 500 }}>{d.title}</span>
                                        <span className="muted small" style={{ display: 'block' }}>
                                            {d.area}
                                        </span>
                                    </td>
                                    {overview.roles.map((r) => (
                                        <td key={r.key} className="center">
                                            <Cell cell={gridCell(overview, d.key, r.key)} />
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                        <tfoot>
                            <tr>
                                <td className="muted small">Exportar</td>
                                {overview.roles.map((r) => (
                                    <td key={r.key} className="center muted small">
                                        {r.exports ? 'Exporta' : 'Não exporta'}
                                    </td>
                                ))}
                            </tr>
                        </tfoot>
                    </table>
                </div>
            )}
        </section>
    )
}
