import { describe, expect, it } from 'vitest'
import {
    canaisDaTabela,
    datasDoPeriodo,
    faixaAtingimento,
    linhasMeta,
    mediaDaColuna,
    metaDoPeriodo,
    progressoMeta,
    somarPorNome,
    rotuloCanal,
    trimestreDe,
} from './comercial.ts'

describe('período da Meta por Atendente', () => {
    it('trimestre da data e datas do período', () => {
        expect(trimestreDe('2026-11-13')).toBe('T4')
        expect(trimestreDe('2026-01-02')).toBe('T1')
        expect(datasDoPeriodo('T4', 2026)).toEqual({ from: '2026-10-01', to: '2026-12-31' })
        expect(datasDoPeriodo('T1', 2028)).toEqual({ from: '2028-01-01', to: '2028-03-31' })
        expect(datasDoPeriodo('S1', 2026)).toEqual({ from: '2026-01-01', to: '2026-06-30' })
    })

    it('meta de 12 mi no trimestre e 24 mi no semestre (v1)', () => {
        expect(metaDoPeriodo('T2')).toBe(12_000_000)
        expect(metaDoPeriodo('S2')).toBe(24_000_000)
    })
})

describe('linhasMeta', () => {
    it('quem mais protocolou primeiro, com o que falta e o %', () => {
        const rows = linhasMeta({ Patricia: 5_380_263.26, Nayla: 7_173_429.13 }, 12_000_000)
        expect(rows.map((r) => r.name)).toEqual(['Nayla', 'Patricia'])
        expect(rows[0].faltam).toBeCloseTo(4_826_570.87, 2)
        expect(Math.floor(rows[0].pct)).toBe(59)
    })

    it('passou da meta: falta 0', () => {
        expect(linhasMeta({ Ana: 13_000_000 }, 12_000_000)[0].faltam).toBe(0)
    })
})

describe('faixas e tabela', () => {
    it('faixa de atingimento da v1', () => {
        expect([faixaAtingimento(100), faixaAtingimento(85), faixaAtingimento(59), faixaAtingimento(10)]).toEqual([
            'ok',
            'accent',
            'warn',
            'danger',
        ])
    })

    it('canais da tabela: geral primeiro, rótulos legíveis', () => {
        const linhas = [
            { atendente: 'Ana', leads_geral: 10, leads_campanha: 4, leads_retorno_ativo: 1, clientes_geral: 2 },
        ]
        expect(canaisDaTabela(linhas).map((c) => c.label)).toEqual(['Geral', 'Campanha', 'Retorno Ativo'])
        expect(rotuloCanal('redes_sociais')).toBe('Redes Sociais')
        expect(
            mediaDaColuna(
                [
                    { atendente: 'A', x: 2 },
                    { atendente: 'B', x: 4 },
                ],
                'x',
            ),
        ).toBe(3)
    })
})

describe('progressoMeta (Meta anual)', () => {
    it('% atingido e quanto falta', () => {
        expect(progressoMeta(234_106_744, 270_000_000).pct).toBeCloseTo(86.706, 2)
        expect(progressoMeta(234_106_744, 270_000_000).faltam).toBe(35_893_256)
    })
    it('passou da meta: 100% e nada faltando', () => {
        expect(progressoMeta(300, 200)).toEqual({ pct: 100, faltam: 0 })
    })
    it('sem meta ou valor inválido: zero', () => {
        expect(progressoMeta(10, 0)).toEqual({ pct: 0, faltam: 0 })
        expect(progressoMeta(Number.NaN, 100)).toEqual({ pct: 0, faltam: 100 })
    })
})

describe('somarPorNome (LexPre + legado)', () => {
    it('soma quem está nos dois e mantém quem está só num', () => {
        expect(somarPorNome({ Ana: 10, Bia: 5 }, { Ana: 2.5, Caio: 1 })).toEqual({ Ana: 12.5, Bia: 5, Caio: 1 })
    })
    it('junta o mesmo nome escrito diferente nos dois bancos (LA: maiúsculas)', () => {
        expect(somarPorNome({ Maria: 100, Jobson: 50 }, { MARIA: 10, JOBSON: 5, 'JOSÉ CARLOS': 1 })).toEqual({
            Maria: 110,
            Jobson: 55,
            'José Carlos': 1,
        })
        expect(somarPorNome({ 'Maria ': 1 }, { María: 2 })).toEqual({ Maria: 3 })
    })
    it('sem legado, igual ao LexPre', () => {
        expect(somarPorNome({ Ana: 10 })).toEqual({ Ana: 10 })
    })
})
