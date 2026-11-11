import { describe, expect, it } from 'vitest'
import { ACORDOS_KPIS, UNIDADES_ACORDOS, camposAcordos, lerAcordos } from './fields.ts'

describe('camposAcordos', () => {
    it.each(UNIDADES_ACORDOS)('%s: todo KPI tem campo com o sufixo da unidade', (unit) => {
        const campos = camposAcordos(unit)
        for (const kpi of ACORDOS_KPIS) expect(campos[kpi]).toMatch(new RegExp(`_${unit}$`))
    })

    it('usa os nomes da v1 (conferidos nas respostas reais)', () => {
        expect(camposAcordos('NG').totalEmExecucao).toBe('total_em_execucao_acordos_NG')
        expect(camposAcordos('LA').atividadesVencidas).toBe('atividades_execucao_vencidas_acordos_LA')
        expect(camposAcordos('RJ').alvaraValorRealizado).toBe('valor_diligencias_expedicao_alvara_execucao_acordos_RJ')
        expect(camposAcordos('NG').pagos).toBe('total_saida_execucao_acordos_periodo_NG')
    })

    it('unidade desconhecida: nenhum campo', () => {
        const campos = camposAcordos('XX')
        for (const kpi of ACORDOS_KPIS) expect(campos[kpi]).toBeNull()
    })
})

describe('lerAcordos', () => {
    it('lê só os campos da unidade pedida', () => {
        const stats = { total_em_execucao_acordos_NG: 50, total_em_execucao_acordos_LA: 19, tre_execucao_acordos_LA: 0 }
        expect(lerAcordos(stats, 'NG').totalEmExecucao).toBe(50)
        expect(lerAcordos(stats, 'LA').totalEmExecucao).toBe(19)
        expect(lerAcordos(stats, 'LA').tre).toBe(0) // zero é valor, não ausência
        expect(lerAcordos(stats, 'RJ').totalEmExecucao).toBeUndefined()
    })

    it('stats vazio (mock) ou valores não numéricos: tudo undefined', () => {
        const vazio = lerAcordos({}, 'NG')
        for (const kpi of ACORDOS_KPIS) expect(vazio[kpi]).toBeUndefined()
        expect(lerAcordos({ total_em_execucao_acordos_NG: null }, 'NG').totalEmExecucao).toBeUndefined()
    })
})
