import { describe, expect, it } from 'vitest'
import { marketingNgFor } from '../../../services/mock/marketingNg.ts'
import { DIMENSOES, GRAFICOS_DA_DIMENSAO } from './marketingComum.ts'
import { PREFIXO_NG, lerMarketingNg, marketingNgFilters } from './marketingNg.ts'

describe('Marketing (banco NG)', () => {
    it('gráficos soltos na resposta, como a v1; rubricas RA x NG', () => {
        const meta = { unit: 'NG' } as never
        const ler = lerMarketingNg({
            meta,
            stats: { [PREFIXO_NG + 'campanha_ra']: 3 },
            [PREFIXO_NG + 'dispositivo']: [{ name: 'Mobile', value: 5 }],
            [PREFIXO_NG + 'rubrica_campanha']: [{ name: 'MORA', ra: 1, ng: 2 }],
        })
        expect(ler.n('campanha_ra')).toBe(3)
        expect(ler.serie('dispositivo')).toEqual([{ name: 'Mobile', value: 5 }])
        expect(ler.rubricasRaNg('rubrica_campanha')).toEqual([{ name: 'MORA', ra: 1, ng: 2 }])
    })

    it('todas as dimensões, com o dispositivo', () => {
        const campos = marketingNgFilters(marketingNgFor('NG'))
        expect(campos.map((f) => f.key)).toEqual(Object.keys(DIMENSOES))
        expect(campos.find((f) => f.key === 'dispositivo_marketing')?.options.map((o) => o.value)).toEqual([
            'Mobile',
            'Desktop',
        ])
    })

    it('o mock traz todos os gráficos clicáveis que a página lê', () => {
        const ler = lerMarketingNg(marketingNgFor('NG'))
        for (const graficos of Object.values(GRAFICOS_DA_DIMENSAO))
            for (const g of graficos) expect(ler.serie(g).length + ler.rubricasRaNg(g).length, g).toBeGreaterThan(0)
    })

    it('fora da NG, só o meta (a v1 só tinha a NG)', () => {
        expect(lerMarketingNg(marketingNgFor('LA_AM')).temDados).toBe(false)
    })
})
