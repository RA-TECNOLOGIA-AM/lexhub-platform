import { describe, expect, it } from 'vitest'
import { comissaoReplicas, filtrosReplicas, lerReplicas, type ReplicasResponse } from './replicas.ts'

const meta = { unit: 'NG', from: '2026-11-01', to: '2026-11-19', source: 'LexFlow', synced_at: null, timezone: 'x' }

const resposta = (unidade: 'NG' | 'LA' | 'RJ'): ReplicasResponse => ({
    meta,
    unidade,
    stats: {
        total_atividades_replicas_NG: 99,
        total_por_prazo_replicas_NG: 75,
        replicas_taxa_procedencia_NG: 16.7,
        replicas_procedencia_procedentes_NG: 1,
        replicas_procedencia_total_decididos_NG: 6,
    },
    replicas_demandas_por_funcionario_NG: [
        { name: 'Bia', encerrado_cumprido: 0, encerrado_nao_cumprido: 1, total: 1 },
        { name: 'Ana', encerrado_cumprido: 82, encerrado_nao_cumprido: 4, total: 86 },
    ],
    replicas_atividades_lista_filtros_opcoes_NG: { funcionarios: ['Bia', 'Ana'], atividades: ['ELABORAR RÉPLICA'] },
})

describe('lerReplicas', () => {
    it('as duas visões e a taxa de procedência (nomes da NG nas duas unidades)', () => {
        const r = lerReplicas(resposta('LA'))
        expect(r.visoes.concluidas.cards.total).toBe(99)
        expect(r.visoes.por_prazo.cards.total).toBe(75)
        expect(r.procedencia).toMatchObject({ taxa: 16.7, procedentes: 1, decididos: 6 })
        expect(r.funcionarios).toEqual(['Ana', 'Bia'])
    })
})

describe('comissão (só LA, R$ 1,50 por réplica concluída)', () => {
    it('LA: quem encerrou como cumprida, × 1,50', () => {
        const t = comissaoReplicas(resposta('LA'))!
        expect(t.title).toBe('Comissionamento — Réplicas LA')
        expect(t.rows).toEqual([{ funcionario: 'Ana', qtd_pecas: 82, valor_unitario: 1.5, valor_comissao: 123 }])
    })
    it('NG e RJ: sem comissão (como a v1; o RJ segue o NG)', () => {
        expect(comissaoReplicas(resposta('NG'))).toBeUndefined()
        expect(comissaoReplicas(resposta('RJ'))).toBeUndefined()
        expect(lerReplicas(resposta('RJ')).unidade).toBe('RJ')
    })
})

describe('filtros', () => {
    it('funcionários, atividade (vem do gráfico) e situação do processo', () => {
        expect(filtrosReplicas(resposta('NG')).map((f) => f.key)).toEqual([
            'funcionario_replicas',
            'atividade_replicas',
            'situacao_processo',
        ])
        expect(filtrosReplicas({ meta })).toEqual([])
    })
})
