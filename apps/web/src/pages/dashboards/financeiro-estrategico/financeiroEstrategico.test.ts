import { describe, expect, it } from 'vitest'
import { barrasReflexo, colunasPrevisao, seriesPorAno } from './financeiroEstrategico.ts'
import type { Previsao } from './types.ts'

describe('seriesPorAno', () => {
    it('uma linha por ano, jan–dez, mês sem TED vazio', () => {
        const s = seriesPorAno(
            [
                { ano: 2026, mes: 11, entradas: 81, receita: 429388.39, ticket_medio: 5301.09 },
                { ano: 2025, mes: 1, entradas: 2, receita: 100, ticket_medio: 50 },
                { ano: 2025, mes: 2, entradas: 0, receita: 0, ticket_medio: 0 },
            ],
            'receita',
        )
        expect(s.map((x) => x.ano)).toEqual([2025, 2026])
        expect(s[0].valores.slice(0, 3)).toEqual([100, null, null])
        expect(s[1].valores[10]).toBe(429388.39)
    })
})

describe('barrasReflexo', () => {
    it('rótulo mês/ano e o ano do filtro; sem data vira "Sem data"', () => {
        expect(
            barrasReflexo([
                { ano: null, mes: null, entradas: 3, receita: 10 },
                { ano: 2023, mes: 4, entradas: 1, receita: 20 },
            ]),
        ).toEqual([
            { rotulo: 'Sem data', ano: 'Sem data', receita: 10, entradas: 3 },
            { rotulo: 'Abr / 2023', ano: '2023', receita: 20, entradas: 1 },
        ])
    })
})

describe('colunasPrevisao', () => {
    it('anos fechados, o atual (até hoje + o que falta) e o previsto (base + faixa)', () => {
        const p = {
            ano_atual: 2026,
            ano_previsto: 2027,
            receita_anual_real: [
                { ano: 2025, receita: 3 },
                { ano: 2026, receita: 4.9 },
            ],
            ano_atual_ate_hoje: 4.9,
            ano_atual_estimado: 5.9,
            cenarios: [{ id: 'tendencia', valor: 9.7 }],
            cenario_base: 'tendencia',
            faixa: { minimo: 9.7, maximo: 11 },
        } as unknown as Previsao
        const c = colunasPrevisao(p)
        expect(c.anos).toEqual(['2025', '2026', '2027'])
        expect(c.real).toEqual([3, 4.9, 0])
        expect(c.restante[1]).toBeCloseTo(1, 6)
        expect(c.previsto).toEqual([0, 0, 9.7])
        expect(c.faixa[2]).toBeCloseTo(1.3, 6)
    })
})
