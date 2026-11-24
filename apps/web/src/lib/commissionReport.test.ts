import { describe, expect, it } from 'vitest'
import { COL_COMISSAO, COL_FUNCIONARIO, commissionHtml } from './commissionReport.ts'
import { fmt } from './format.ts'

const base = {
    title: 'Comissão — Protocolo (LexPre)',
    unit: 'NG',
    from: '2026-11-01',
    to: '2026-11-13',
    generatedAt: new Date(2026, 10, 13, 17, 29, 18),
    columns: [COL_FUNCIONARIO, { key: 'qtd', label: 'Protocolados', format: fmt.int, sum: true }, COL_COMISSAO],
    sortBy: 'valor_comissao',
}

describe('commissionHtml', () => {
    it('linhas da maior comissão à menor, total das colunas somáveis e período em pt-BR', () => {
        const html = commissionHtml({
            ...base,
            rows: [
                { funcionario: 'Ana', qtd: 10, valor_comissao: 10 },
                { funcionario: 'Raimunda Moura', qtd: 168, valor_comissao: 168 },
            ],
        })
        expect(html.indexOf('Raimunda Moura')).toBeLessThan(html.indexOf('Ana'))
        expect(html).toContain('01/11/2026 a 13/11/2026')
        expect(html).toMatch(/<td>Total<\/td><td class="n">178<\/td><td class="n">R\$\s178,00/)
    })

    it('coluna sem soma fica vazia no total; valor ausente vira —', () => {
        const html = commissionHtml({
            ...base,
            columns: [COL_FUNCIONARIO, { key: 'taxa', label: 'Taxa', format: fmt.pct }, COL_COMISSAO],
            rows: [{ funcionario: 'Ana', taxa: null, valor_comissao: 5 }],
        })
        expect(html).toContain('<td class="n">—</td>')
        expect(html).toMatch(/<td>Total<\/td><td><\/td>/)
    })

    it('escapa o que vem dos dados', () => {
        const html = commissionHtml({ ...base, rows: [{ funcionario: '<b>x</b>', qtd: 1, valor_comissao: 1 }] })
        expect(html).toContain('&lt;b&gt;x&lt;/b&gt;')
        expect(html).not.toContain('<b>x</b>')
    })

    it('sem linhas: avisa no lugar da tabela', () => {
        expect(commissionHtml({ ...base, rows: [] })).toContain('Sem comissão no período.')
    })

    it('detalhe sem quebra de página fica embaixo da comissão', () => {
        const html = commissionHtml({
            ...base,
            rows: [{ funcionario: 'Isabelle', qtd: 1, valor_comissao: 13 }],
            details: {
                title: 'Demandas canceladas',
                breakBefore: false,
                columns: [
                    { key: 'materia', label: 'Matéria' },
                    { key: 'data', label: 'Cancelado em' },
                    { key: 'atendente', label: 'Atendente comercial' },
                    { key: 'desconto', label: 'Desconto', format: fmt.brl, sum: true },
                ],
                rows: [{ materia: 'MORA', data: '10/11/2026', atendente: 'Isabelle', desconto: 13 }],
            },
        })
        expect(html).toContain('<section class="detalhes continua">')
        expect(html).toContain('<h2>Demandas canceladas</h2>')
        expect(html).toContain('MORA')
        expect(html).toContain('10/11/2026')
        expect(html).toContain('Isabelle')
        const fimDaComissao = html.indexOf('</tfoot>')
        const secao = html.indexOf('<section class="detalhes continua">')
        expect(secao).toBeGreaterThan(fimDaComissao)
        expect(html.indexOf('Demandas canceladas')).toBeLessThan(html.indexOf('Gerado pelo LexHub'))
    })

    it('sem demandas canceladas, a segunda tabela não aparece', () => {
        const html = commissionHtml({
            ...base,
            rows: [{ funcionario: 'Ana', qtd: 1, valor_comissao: 1 }],
            details: {
                title: 'Demandas canceladas',
                breakBefore: false,
                columns: [{ key: 'materia', label: 'Matéria' }],
                rows: [],
            },
        })
        expect(html).not.toContain('Demandas canceladas')
    })
})
