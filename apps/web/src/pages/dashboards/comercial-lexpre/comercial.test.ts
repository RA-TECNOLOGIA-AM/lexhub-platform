import { describe, expect, it } from 'vitest'
import {
    canaisDaTabela,
    datasDoPeriodo,
    faixaAtingimento,
    linhasMeta,
    mediaDaColuna,
    metaDoPeriodo,
    hojeEmManaus,
    progressoMeta,
    projecaoPrevia,
    ritmoMeta,
    taxaCancelamento,
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

describe('ritmoMeta (ritmo da meta anual)', () => {
    // O exemplo do modal: R$ 270 mi em 2026, hoje 23/11/2026, R$ 239.255.589 realizados.
    const r = ritmoMeta(239_255_589, 270_000_000, 2026, '2026-11-23')

    it('esperado até hoje: linear pelos dias do ano, contando hoje', () => {
        expect(r.diasNoAno).toBe(365)
        expect(r.decorridos).toBe(327)
        expect(r.restantes).toBe(38)
        expect(Math.round(r.mediaPlanejada)).toBe(739_726)
        expect(Math.round(r.esperado)).toBe(241_890_411)
        expect(r.pctEsperado).toBeCloseTo(89.59, 2)
    })

    it('comparativo com o realizado e o ritmo para fechar o ano', () => {
        expect(r.pctRealizado).toBeCloseTo(88.61, 2)
        expect(Math.round(r.diferenca)).toBe(-2_634_822)
        expect(r.pontos).toBeCloseTo(-0.98, 2)
        expect(r.faltam).toBe(30_744_411)
        expect(Math.round(r.novaMedia ?? 0)).toBe(809_063)
        expect(r.variacao).toBeCloseTo(0.0937, 4)
        expect(r.dias).toBeCloseTo(-3.56, 2) // 2.634.822 ÷ 739.726 por dia
        expect(r.status).toBe('ligeiramente_atrasado')
    })

    it('status: atrasado a partir de 2 p.p., adiantado no ritmo ou à frente, atingida sem faltar nada', () => {
        expect(ritmoMeta(200_000_000, 270_000_000, 2026, '2026-11-23').status).toBe('atrasado')
        expect(ritmoMeta(250_000_000, 270_000_000, 2026, '2026-11-23').status).toBe('adiantado')
        expect(ritmoMeta(270_000_000, 270_000_000, 2026, '2026-11-23').status).toBe('atingida')
    })

    it('ano bissexto, ano que não começou e ano que acabou', () => {
        expect(ritmoMeta(0, 366, 2028, '2028-12-31')).toMatchObject({ diasNoAno: 366, decorridos: 366, restantes: 0 })
        expect(ritmoMeta(0, 100, 2027, '2026-11-23')).toMatchObject({ decorridos: 0, esperado: 0, restantes: 365 })
        expect(ritmoMeta(10, 100, 2025, '2026-01-05')).toMatchObject({
            decorridos: 365,
            novaMedia: null,
            variacao: null,
        })
    })

    it('hoje em Manaus (UTC−4), não no fuso do navegador', () => {
        expect(hojeEmManaus(new Date('2026-11-24T03:30:00Z'))).toBe('2026-11-23')
        expect(hojeEmManaus(new Date('2026-11-24T04:30:00Z'))).toBe('2026-11-24')
    })
})

describe('taxaCancelamento (card Cancelados)', () => {
    it('canceladas ÷ fechadas no período, em %', () => {
        expect(taxaCancelamento(38, 747)).toBeCloseTo(5.087, 3)
        expect(taxaCancelamento(0, 10)).toBe(0)
    })
    it('sem ação fechada não há base: null', () => {
        expect(taxaCancelamento(5, 0)).toBeNull()
        expect(taxaCancelamento(Number.NaN, 10)).toBeNull()
    })
})

describe('projecaoPrevia (prévia dos represados no Ritmo da meta)', () => {
    it('quanto do que falta a prévia cobre e onde o ano iria parar', () => {
        const p = projecaoPrevia(3_463_828, { realizado: 239_255_589, faltam: 30_744_411 }, 270_000_000)
        expect(p.cobreFalta).toBeCloseTo(11.27, 2)
        expect(p.pctComPrevia).toBeCloseTo(89.9, 1)
        expect(p.fechaMeta).toBe(false)
    })
    it('prévia maior que o que falta fecha a meta; meta já atingida não tem o que cobrir', () => {
        expect(projecaoPrevia(50, { realizado: 60, faltam: 40 }, 100).fechaMeta).toBe(true)
        expect(projecaoPrevia(10, { realizado: 100, faltam: 0 }, 100).cobreFalta).toBeNull()
    })
})
