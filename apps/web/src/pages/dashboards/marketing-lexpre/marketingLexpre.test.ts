import { describe, expect, it } from 'vitest'
import { marketingLexpreFor } from '../../../services/mock/marketingLexpre.ts'
import { GRAFICOS_DA_DIMENSAO } from '../marketing/marketingComum.ts'
import { DIMENSOES_LEXPRE, PREFIXO, lerMarketing, marketingFilters } from './marketingLexpre.ts'

describe('Marketing (LexPre)', () => {
    it('lê stats e charts com o prefixo marketing_lexpre_ng_', () => {
        const meta = { unit: 'NG' } as never
        const { n, serie } = lerMarketing({
            meta,
            stats: { [PREFIXO + 'total_clientes']: 12 },
            charts: { [PREFIXO + 'genero']: [{ name: 'FEMININO', value: 7 }] },
        })
        expect(n('total_clientes')).toBe(12)
        expect(serie('genero')).toEqual([{ name: 'FEMININO', value: 7 }])
    })

    it('filtros clicáveis sem o dispositivo (não existe no LexPre)', () => {
        const campos = marketingFilters(marketingLexpreFor('NG'))
        expect(campos.map((f) => f.key)).toEqual(DIMENSOES_LEXPRE)
        expect(campos.map((f) => f.key)).not.toContain('dispositivo_marketing')
        expect(campos.find((f) => f.key === 'genero_marketing')?.options.map((o) => o.value)).toEqual([
            'FEMININO',
            'MASCULINO',
        ])
    })

    it('o mock traz todos os gráficos clicáveis que a página lê', () => {
        const { serie } = lerMarketing(marketingLexpreFor('NG'))
        for (const dim of DIMENSOES_LEXPRE)
            for (const g of GRAFICOS_DA_DIMENSAO[dim].filter((g) => g !== 'ind_rubricas'))
                expect(serie(g).length, g).toBeGreaterThan(0)
    })

    it('LA sem anúncios (a conta dela não é ingerida, como na v1)', () => {
        const { n, investimento } = lerMarketing(marketingLexpreFor('LA_AM'))
        expect(n('total_clientes')).toBeGreaterThan(0)
        expect(n('facebook_valor_gasto')).toBe(0)
        expect(investimento).toEqual([])
    })
})
