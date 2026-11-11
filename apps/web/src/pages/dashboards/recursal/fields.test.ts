import { describe, expect, it } from 'vitest'
import { pickRecursal, RECURSAL_KPIS, recursalFields } from './fields.ts'

// Trechos das respostas reais da v1 (/recursal_NG e /recursal_LA, mês anterior).
const STATS_NG = {
    total_recursal_NG: 5077,
    entrada_recursal_NG: 828,
    total_decisoes_recursal_NG: 458,
    percent_mantido_perda_recursal_NG: 51.5,
    atividades_recursos_vencidas_NG: 241,
    provimento_mensal_qtd_NG: 139,
    provimento_mensal_meta_NG: 80,
    total_recursal_LA: null,
}
const STATS_LA = {
    total_recursal_LA: 6990,
    entrada_recursal_LA: 621,
    total_decisoes_recursal_LA: 250,
    percent_mantido_perda_recursal_LA: 39.2,
    atividades_recursos_vencidas_LA: 2,
    total_recursal_NG: null,
}

describe('recursalFields', () => {
    it('NG: todos os KPIs com sufixo _NG', () => {
        const f = recursalFields('NG')
        for (const kpi of RECURSAL_KPIS) expect(f[kpi]).toMatch(/_NG$/)
        expect(f.estoque).toBe('total_recursal_NG')
        expect(f.mantidoGanhoPct).toBe('percent_mantido_ganho_recursal_NG')
        expect(f.provimentoMeta).toBe('provimento_mensal_meta_NG')
    })

    it('LA: sufixo _LA; meta de provimento não existe', () => {
        const f = recursalFields('LA')
        expect(f.estoque).toBe('total_recursal_LA')
        expect(f.atividadesVencemHoje).toBe('atividades_recursos_vencem_hoje_LA')
        expect(f.provimentoQtd).toBeNull()
        expect(f.provimentoMeta).toBeNull()
    })

    it('unidade desconhecida: nenhum campo', () => {
        const f = recursalFields('RJ')
        for (const kpi of RECURSAL_KPIS) expect(f[kpi]).toBeNull()
    })
})

describe('pickRecursal', () => {
    it('lê os valores da unidade certa', () => {
        const ng = pickRecursal(STATS_NG, 'NG')
        expect(ng.estoque).toBe(5077)
        expect(ng.mantidoPerdaPct).toBe(51.5)
        expect(ng.provimentoQtd).toBe(139)

        const la = pickRecursal(STATS_LA, 'LA')
        expect(la.estoque).toBe(6990)
        expect(la.atividadesVencidas).toBe(2)
        expect(la.provimentoQtd).toBeNull()
    })

    it('mock (stats vazio ou ausente): tudo null', () => {
        for (const stats of [{}, undefined]) {
            const v = pickRecursal(stats, 'NG')
            for (const kpi of RECURSAL_KPIS) expect(v[kpi]).toBeNull()
        }
    })
})
