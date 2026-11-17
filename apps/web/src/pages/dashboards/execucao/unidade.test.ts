import { describe, expect, it } from 'vitest'
import { nomeNaUnidade, unidadeAcordos, unidadeExecucao } from './unidade.ts'

const meta = { unit: 'LA', from: '2026-11-01', to: '2026-11-17', source: 'LexFlow', synced_at: null, timezone: 'x' }

describe('nomeNaUnidade (a mesma regra de generico_v1.nome_na_unidade na API)', () => {
    it('troca o _NG, acrescenta onde não tem e cuida do _detalhe', () => {
        expect(nomeNaUnidade('execucao_resolvidos_por_dia_NG', 'LA')).toBe('execucao_resolvidos_por_dia_LA')
        expect(nomeNaUnidade('tre', 'RJ')).toBe('tre_RJ')
        expect(nomeNaUnidade('total_valor_execucao_vazio_detalhe', 'LA')).toBe('total_valor_execucao_vazio_LA_detalhe')
        expect(nomeNaUnidade('total_valor_alcada_final_vazio_acordos_NG_detalhe', 'RJ')).toBe(
            'total_valor_alcada_final_vazio_acordos_RJ_detalhe',
        )
    })
    it('na NG e nos campos novos da V2 (_historico), o nome não muda', () => {
        expect(nomeNaUnidade('tre', 'NG')).toBe('tre')
        expect(nomeNaUnidade('total_em_execucao_historico', 'LA')).toBe('total_em_execucao_historico')
    })
})

describe('unidade pela rota da v1', () => {
    it('Execução e Acordos', () => {
        expect(unidadeExecucao({ meta, dashboard: 'execucao' })).toBe('NG')
        expect(unidadeExecucao({ meta, dashboard: 'execucao_RJ' })).toBe('RJ')
        expect(unidadeExecucao({ meta, dashboard: 'execucao_acordos_LA' })).toBeNull()
        expect(unidadeAcordos({ meta, dashboard: 'execucao_acordos_LA' })).toBe('LA')
        expect(unidadeAcordos({ meta })).toBeNull()
    })
})
