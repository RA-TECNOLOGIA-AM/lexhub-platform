// Módulo: linhas -> texto CSV que o Excel em português abre certo, sem React (testado em csv.test.ts).
// No mock é o front que gera o arquivo; com a API, quem gera é o servidor (como na v1).
// Regras: ';' separa as colunas (no Brasil a vírgula é decimal), BOM no começo (o Excel lê os acentos certo)
// e CRLF entre linhas (o padrão do Windows/Excel).

export type CsvColumn = { key: string; label: string }

// Valor com ; aspas ou quebra de linha vai entre aspas, e aspas internas viram duas ("").
function escape(value: unknown): string {
    const text = value === null || value === undefined ? '' : String(value)
    return /[;"\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}

export function toCsv(columns: CsvColumn[], rows: Record<string, unknown>[]): string {
    const header = columns.map((c) => escape(c.label))
    const lines = rows.map((row) => columns.map((c) => escape(row[c.key])))
    return '\uFEFF' + [header, ...lines].map((cells) => cells.join(';')).join('\r\n')
}
