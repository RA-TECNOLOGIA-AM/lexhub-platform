import type { ReactNode } from 'react'

export type Column<T> = {
    header: string
    render: (row: T) => ReactNode
    align?: 'left' | 'right'
}

type DataTableProps<T> = {
    columns: Column<T>[]
    rows: T[]
    rowKey: (row: T) => string
    empty?: string // texto quando não há linhas
}

// Módulo: tabela a partir de colunas. Quem usa diz o que vai em cada coluna; a tabela só desenha.
export function DataTable<T>({ columns, rows, rowKey, empty = 'Nada para mostrar.' }: DataTableProps<T>) {
    return (
        <div className="card" style={{ overflow: 'hidden' }}>
            <div className="tblwrap">
                <table className="tbl">
                    <thead>
                        <tr>
                            {columns.map((c) => (
                                <th key={c.header} className={c.align === 'right' ? 'num' : undefined}>
                                    {c.header}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.length === 0 ? (
                            <tr>
                                <td colSpan={columns.length} className="muted">
                                    {empty}
                                </td>
                            </tr>
                        ) : (
                            rows.map((row) => (
                                <tr key={rowKey(row)}>
                                    {columns.map((c) => (
                                        <td key={c.header} className={c.align === 'right' ? 'num' : undefined}>
                                            {c.render(row)}
                                        </td>
                                    ))}
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
