import { describe, expect, it } from 'vitest'
import { linhasValorRubricas, proximaOrdem } from './comissao.ts'

const pontos = [
    { name: 'CESTA', value: 48 },
    { name: 'ANP', value: 65 },
    { name: 'NOVA', value: 2 },
]
const tabela = [
    { rubrica: 'anp', acoes: 65, valor_am: 1, total: 65 },
    { rubrica: 'CESTA', acoes: 48, valor_am: 3, total: 144 },
]

describe('linhasValorRubricas', () => {
    it('casa o valor pelo nome (sem caixa) e soma os totais', () => {
        const r = linhasValorRubricas(pontos, tabela, { key: 'acoes', dir: 'desc' })
        expect(r.linhas.map((l) => [l.rubrica, l.acoes, l.valorAm, l.total])).toEqual([
            ['ANP', 65, 1, 65],
            ['CESTA', 48, 3, 144],
            ['NOVA', 2, null, null],
        ])
        expect(r.totalAcoes).toBe(115)
        expect(r.totalValor).toBe(209)
    })
    it('ordena por rubrica', () => {
        const r = linhasValorRubricas(pontos, tabela, { key: 'rubrica', dir: 'asc' })
        expect(r.linhas.map((l) => l.rubrica)).toEqual(['ANP', 'CESTA', 'NOVA'])
    })
})

describe('proximaOrdem', () => {
    it('a mesma coluna inverte; outra começa no padrão dela', () => {
        expect(proximaOrdem({ key: 'acoes', dir: 'desc' }, 'acoes')).toEqual({ key: 'acoes', dir: 'asc' })
        expect(proximaOrdem({ key: 'acoes', dir: 'desc' }, 'rubrica')).toEqual({ key: 'rubrica', dir: 'asc' })
        expect(proximaOrdem({ key: 'rubrica', dir: 'asc' }, 'acoes')).toEqual({ key: 'acoes', dir: 'desc' })
    })
})
