import type { ReactNode } from 'react'

export type Column<T> = {
    header: ReactNode // texto, ou um botão (ex.: ordenar pela coluna)
    render: (row: T) => ReactNode
    align?: 'left' | 'right'
}

type DataTableProps<T> = {
    columns: Column<T>[]
    rows: T[]
    rowKey: (row: T) => string
    empty?: string // texto quando não há linhas
    rowClassName?: (row: T) => string | undefined // classe de uma linha (ex.: destacar a sessão de suporte)
}

// Módulo: tabela a partir de colunas. Quem usa diz o que vai em cada coluna; a tabela só desenha.
export function DataTable<T>({ columns, rows, rowKey, empty = 'Nada para mostrar.', rowClassName }: DataTableProps<T>) {
    return (
        <div className="card" style={{ overflow: 'hidden' }}>
            <div className="tblwrap">
                <table className="tbl">
                    <thead>
                        <tr>
                            {columns.map((c, i) => (
                                <th key={i} className={c.align === 'right' ? 'num' : undefined}>
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
                                <tr key={rowKey(row)} className={rowClassName?.(row)}>
                                    {columns.map((c, i) => (
                                        <td key={i} className={c.align === 'right' ? 'num' : undefined}>
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
