import { describe, expect, it } from 'vitest'
import { pendenciasLegadoFor } from '../../../services/mock/pendenciasLegado.ts'
import { lerPendencias } from './pendencias.ts'

const meta = { unit: 'NG', from: '2026-11-01', to: '2026-11-16', source: 'NG', synced_at: null, timezone: 'x' }

describe('lerPendencias', () => {
    it('lê a rota da NG (/pendencias) no formato das Pendências (LexPre)', () => {
        const p = lerPendencias({
            meta,
            dashboard: 'pendencias',
            stats: {
                pendencias_total: 2,
                pendencias_nao_resolvidas: 5,
                pendencias_resolvidas_reajuizamento: 0,
                comparativo_tempo_medio_pendencias_resolvidas: 12.5,
                pendencias_total_LA: null, // a resposta da v1 traz os campos da LA vazios
            },
            pendencias_nao_resolvidas_por_origem: [{ name: 'RETORNO COMERCIAL', value: 5 }],
        } as never)
        expect(p.stats.pendencias_total).toBe(2)
        expect(p.stats.pendencias_nao_resolvidas).toBe(5)
        expect(p.stats.pendencias_resolvidas_reajuizamento).toBe(0)
        expect(p.stats.comparativo_tempo_medio_resolvidos_pendencia).toBe(12.5)
        expect(p.pendencias_nao_resolvidas_por_origem).toEqual([{ name: 'RETORNO COMERCIAL', value: 5 }])
    })

    it('lê a rota da LA (/pendencia_LA): _LA nos nomes, sem reajuizamento nem comparativos', () => {
        const p = lerPendencias(pendenciasLegadoFor('LA_AM', { org: 'lexgroup', unit: 'LA_AM' }))
        expect(p.stats.pendencias_total).toBe(9)
        expect(p.stats.pendencias_nao_resolvidas).toBe(8)
        expect(p.stats.pendencias_taxa_resolvidos).toBe(11.11)
        expect(p.stats.pendencias_nao_resolvidas_reajuizamento).toBeUndefined()
        expect(p.stats.comparativo_pendencias_resolvidas).toBeNull()
        expect(p.media_pendencias_resolvidas_por_funcionario).toEqual([{ name: 'RENATA APARECIDA', value: 1 }])
        expect(p.comissionamento_pendencias_por_funcionario[0].funcionario).toBe('RENATA APARECIDA')
    })

    it('funcionários do filtro sem repetir a mesma pessoa com o nome completo', () => {
        const p = lerPendencias(pendenciasLegadoFor('NG', { org: 'lexgroup', unit: 'NG' }))
        expect(p.opcoes_filtro?.funcionarios).toEqual(['JOÃO VICTOR', 'LETÍCIA ROBERTA'])
    })
})
