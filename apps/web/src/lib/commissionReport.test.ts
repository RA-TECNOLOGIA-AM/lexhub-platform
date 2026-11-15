import { describe, expect, it } from 'vitest'
import { commissionHtml } from './commissionReport.ts'

const base = {
    title: 'Comissão — Protocolo (LexPre)',
    unit: 'Nicolas Gomes (NG)',
    from: '2026-11-01',
    to: '2026-11-13',
    quantityLabel: 'Protocolados',
    generatedAt: new Date(2026, 10, 13, 17, 29, 18),
}

describe('commissionHtml', () => {
    it('linhas do maior valor ao menor, total e período em pt-BR', () => {
        const html = commissionHtml({
            ...base,
            rows: [
                { funcionario: 'Ana', quantidade: 10, valor: 10 },
                { funcionario: 'Raimunda Moura', quantidade: 168, valor: 168 },
            ],
        })
        expect(html.indexOf('Raimunda Moura')).toBeLessThan(html.indexOf('Ana'))
        expect(html).toContain('01/11/2026 a 13/11/2026')
        expect(html).toMatch(/Total<\/td><td class="n">178<\/td><td class="n">R\$\s178,00/)
    })

    it('escapa o que vem dos dados', () => {
        const html = commissionHtml({ ...base, rows: [{ funcionario: '<b>x</b>', quantidade: 1, valor: 1 }] })
        expect(html).toContain('&lt;b&gt;x&lt;/b&gt;')
        expect(html).not.toContain('<b>x</b>')
    })

    it('sem linhas: avisa no lugar da tabela', () => {
        expect(commissionHtml({ ...base, rows: [] })).toContain('Sem comissão no período.')
    })
})
