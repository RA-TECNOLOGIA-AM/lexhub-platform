import { fmt } from './format.ts'

// Módulo: o relatório de comissão de um dashboard em HTML pronto para imprimir (sem React; testado em
// commissionReport.test.ts). Quem chama manda o HTML para a impressão do navegador ("Salvar como PDF").

export type CommissionCell = string | number | null

// Uma coluna: de onde vem o valor, como mostrar e se soma na linha Total.
export type CommissionColumn = {
    key: string
    label: string
    format?: (v: number) => string // sem = texto (ex.: o nome); com = número alinhado à direita
    sum?: boolean // entra na linha Total
}

export type CommissionTable = {
    columns: CommissionColumn[]
    rows: Record<string, CommissionCell>[]
    sortBy: string // coluna que ordena (maior primeiro), em geral a comissão
    title?: string // título próprio do relatório (senão, "Comissão — <dashboard>")
    notes?: string[] // linhas embaixo do período (ex.: a meta de qualidade do Recursal)
    // Uma segunda tabela, numa página nova, na ordem recebida (ex.: o detalhamento dos descontos do Recursal).
    details?: { title: string; warning?: string; columns: CommissionColumn[]; rows: Record<string, CommissionCell>[] }
}

export type CommissionReport = CommissionTable & {
    title: string // "Comissão — Protocolo (LexPre)"
    unit: string // "NG"
    from: string // AAAA-MM-DD
    to: string
    generatedAt: Date
}

const esc = (s: string) =>
    s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] ?? c)

// '2026-11-04' -> '04/11/2026'
const dia = (iso: string) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
    return m ? `${m[3]}/${m[2]}/${m[1]}` : iso
}

const num = (v: CommissionCell) => (typeof v === 'number' ? v : 0)

function cell(col: CommissionColumn, v: CommissionCell): string {
    if (!col.format) return `<td>${esc(String(v ?? ''))}</td>`
    return `<td class="n">${v === null || v === undefined ? '—' : esc(col.format(num(v)))}</td>`
}

// A segunda tabela (opcional), numa página nova.
function detalhes(r: CommissionReport): string {
    const d = r.details
    if (!d || d.rows.length === 0) return ''
    const head = d.columns.map((c) => `<th${c.format ? ' class="n"' : ''}>${esc(c.label)}</th>`).join('')
    const body = d.rows.map((row) => `<tr>${d.columns.map((c) => cell(c, row[c.key])).join('')}</tr>`).join('')
    return `
<section class="detalhes">
<h1>${esc(d.title)}</h1>
${d.warning ? `<p class="aviso">${esc(d.warning)}</p>` : ''}
<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>
</section>`
}

export function commissionHtml(r: CommissionReport): string {
    const textKey = r.columns.find((c) => !c.format)?.key
    const rows = [...r.rows].sort(
        (a, b) =>
            num(b[r.sortBy]) - num(a[r.sortBy]) ||
            String(textKey ? a[textKey] : '').localeCompare(String(textKey ? b[textKey] : '')),
    )
    const head = r.columns.map((c) => `<th${c.format ? ' class="n"' : ''}>${esc(c.label)}</th>`).join('')
    const body = rows.map((row) => `<tr>${r.columns.map((c) => cell(c, row[c.key])).join('')}</tr>`).join('')
    const total = r.columns
        .map((c, i) => {
            if (i === 0) return '<td>Total</td>'
            if (!c.sum || !c.format) return '<td></td>'
            return `<td class="n">${esc(c.format(rows.reduce((sum, row) => sum + num(row[c.key]), 0)))}</td>`
        })
        .join('')
    const gerado = r.generatedAt.toLocaleString('pt-BR')
    return `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8" /><title>${esc(r.title)} · ${esc(r.unit)}</title>
<style>
  @page { size: A4 ${r.columns.length > 4 ? 'landscape' : 'portrait'}; margin: 14mm; }
  body { font-family: Inter, system-ui, sans-serif; color: #15181d; font-size: 12px; }
  h1 { font-size: 18px; margin: 0 0 4px; }
  .meta { color: #5b6370; margin-bottom: 16px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 7px 8px; border-bottom: 1px solid #e3e6eb; text-align: left; }
  th { font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: #5b6370; }
  .n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
  tfoot td { font-weight: 700; border-top: 2px solid #15181d; border-bottom: 0; }
  .foot { margin-top: 20px; color: #8a93a0; font-size: 10px; }
  .detalhes { page-break-before: always; }
  .aviso { color: #92400e; margin: 4px 0 12px; }
</style></head><body>
<h1>${esc(r.title)}</h1>
<div class="meta">${esc(r.unit)} · Período: ${dia(r.from)} a ${dia(r.to)}${(r.notes ?? []).map((n) => `<br />${esc(n)}`).join('')}</div>
<table>
  <thead><tr>${head}</tr></thead>
  <tbody>${body || `<tr><td colspan="${r.columns.length}">Sem comissão no período.</td></tr>`}</tbody>
  <tfoot><tr>${total}</tr></tfoot>
</table>${detalhes(r)}
<div class="foot">Gerado pelo LexHub em ${esc(gerado)}.</div>
</body></html>`
}

// Imprime o HTML num iframe escondido (sem abrir janela nova, sem bloqueador de pop-up).
// Na janela de impressão, "Salvar como PDF" gera o arquivo.
export function printHtml(html: string) {
    const frame = document.createElement('iframe')
    frame.setAttribute('aria-hidden', 'true')
    frame.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0;'
    document.body.append(frame)
    const doc = frame.contentDocument
    if (!doc || !frame.contentWindow) {
        frame.remove()
        return
    }
    doc.open()
    doc.write(html)
    doc.close()
    const win = frame.contentWindow
    win.focus()
    win.print()
    // print() segura até a janela fechar na maioria dos navegadores; o iframe sai logo depois.
    setTimeout(() => frame.remove(), 1000)
}

// Colunas usadas por mais de um dashboard.
export const COL_FUNCIONARIO: CommissionColumn = { key: 'funcionario', label: 'Funcionário' }
export const COL_COMISSAO: CommissionColumn = { key: 'valor_comissao', label: 'Comissão', format: fmt.brl, sum: true }
