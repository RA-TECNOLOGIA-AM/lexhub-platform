import { fmt } from './format.ts'

// Módulo: o relatório de comissão de um dashboard em HTML pronto para imprimir (sem React; testado em
// commissionReport.test.ts). Quem chama manda o HTML para a impressão do navegador ("Salvar como PDF").

export type CommissionRow = { funcionario: string; quantidade: number; valor: number }

export type CommissionReport = {
    title: string // "Comissão — Protocolo (LexPre)"
    unit: string // "Nicolas Gomes (NG)"
    from: string // AAAA-MM-DD
    to: string
    quantityLabel: string // "Protocolados"
    rows: CommissionRow[]
    generatedAt: Date
}

const esc = (s: string) =>
    s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] ?? c)

// '2026-11-04' -> '04/11/2026'
const dia = (iso: string) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
    return m ? `${m[3]}/${m[2]}/${m[1]}` : iso
}

export function commissionHtml(r: CommissionReport): string {
    const rows = [...r.rows].sort((a, b) => b.valor - a.valor || a.funcionario.localeCompare(b.funcionario))
    const totalQtd = rows.reduce((sum, x) => sum + x.quantidade, 0)
    const totalValor = rows.reduce((sum, x) => sum + x.valor, 0)
    const body = rows
        .map(
            (x) =>
                `<tr><td>${esc(x.funcionario)}</td><td class="n">${fmt.int(x.quantidade)}</td><td class="n">${esc(fmt.brl(x.valor))}</td></tr>`,
        )
        .join('')
    const gerado = r.generatedAt.toLocaleString('pt-BR')
    return `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8" /><title>${esc(r.title)} · ${esc(r.unit)}</title>
<style>
  @page { size: A4; margin: 16mm; }
  body { font-family: Inter, system-ui, sans-serif; color: #15181d; font-size: 12px; }
  h1 { font-size: 18px; margin: 0 0 4px; }
  .meta { color: #5b6370; margin-bottom: 16px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 7px 8px; border-bottom: 1px solid #e3e6eb; text-align: left; }
  th { font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: #5b6370; }
  .n { text-align: right; font-variant-numeric: tabular-nums; }
  tfoot td { font-weight: 700; border-top: 2px solid #15181d; border-bottom: 0; }
  .foot { margin-top: 20px; color: #8a93a0; font-size: 10px; }
</style></head><body>
<h1>${esc(r.title)}</h1>
<div class="meta">${esc(r.unit)} · Período: ${dia(r.from)} a ${dia(r.to)}</div>
<table>
  <thead><tr><th>Funcionário</th><th class="n">${esc(r.quantityLabel)}</th><th class="n">Comissão</th></tr></thead>
  <tbody>${body || '<tr><td colspan="3">Sem comissão no período.</td></tr>'}</tbody>
  <tfoot><tr><td>Total</td><td class="n">${fmt.int(totalQtd)}</td><td class="n">${esc(fmt.brl(totalValor))}</td></tr></tfoot>
</table>
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
