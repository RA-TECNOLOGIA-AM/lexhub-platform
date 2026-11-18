import { describe, expect, it } from 'vitest'
import { julgadosSentencasFor } from '../../../services/mock/julgadosSentencas.ts'
import { lerJulgadosSentencas, sentencasFields, unidadeSentencas } from './fields.ts'
import type { JulgadosSentencasResponse } from './types.ts'

const meta = (unit: string) => ({
    unit,
    from: '2026-10-01',
    to: '2026-10-31',
    source: 'LexFlow',
    synced_at: null,
    timezone: 'America/Manaus',
})

// Trecho no formato da DashboardResponse da rota julgados_RJ da v1 (model_dump).
const RESPOSTA_RJ: JulgadosSentencasResponse = {
    meta: meta('RJ'),
    dashboard: 'julgados_RJ',
    stats: {
        julgados_sentenca_total_RJ: 40,
        julgados_sentenca_procedentes_RJ: 20,
        julgados_sentenca_improcedentes_RJ: 12,
        julgados_sentenca_extintos_RJ: 6,
        julgados_sentenca_valor_procedentes_RJ: 1000.5,
        comparativo_julgados_sentenca_total_RJ: -12.5,
        julgados_extincao_total_estoque_RJ: 90,
        julgados_improcedencia_revertida_2g_estoque_RJ: 7,
        julgados_uf_opcoes_RJ: ['rj '],
        julgados_sentenca_sem_juiz_RJ: 3,
        julgados_sentenca_dados_faltando_RJ: [{ numero_processo: '1', campo: 'Juiz' }],
        julgados_sentenca_total_NG: 999, // de outra unidade: não pode ser lido
    },
    ranking_juizes_sentenca_julgados_RJ: [
        { name: 'Dra. Fulana', initials: 'DF', total_casos: 4, taxa_sucesso: 50, fav: 2, des: 1, outros: 1 },
    ],
    julgados_por_materia_RJ: [{ name: 'ANP', value: 30 }],
    julgados_extincao_por_comarca_estoque_RJ: [{ name: 'Niterói', value: 5, valor_causa: 100, uf: 'rj' }],
    julgados_por_motivo_extincao_RJ: [{ name: 'Desistência', value: 2 }],
    julgados_sentenca_lista_RJ: [
        {
            id: 1,
            numero_processo: '123',
            fase: 'Conhecimento',
            subfase: 'Sentença',
            status_1g: 'Procedente',
            uf: 'RJ',
            juiz: 'Dra. Fulana',
            data_sentenca: '2026-10-05T00:00:00',
            status_sentenca_embargos: '',
            data_sentenca_embargos: null,
        },
    ],
}

describe('Julgados Sentenças: campos e leitura', () => {
    it('a unidade vem da rota da v1; sem ela, do código da unidade', () => {
        expect(unidadeSentencas(RESPOSTA_RJ)).toBe('RJ')
        expect(unidadeSentencas({ meta: meta('LA') })).toBe('LA')
        expect(unidadeSentencas({ meta: meta('CT') })).toBeNull()
    })

    it('os nomes levam o sufixo da unidade', () => {
        const f = sentencasFields('LA')
        expect(f.numeros.total).toBe('julgados_sentenca_total_LA')
        expect(f.comparativos.valorProcedentes).toBe('comparativo_julgados_sentenca_valor_procedentes_LA')
        expect(f.listas.ranking).toBe('ranking_juizes_sentenca_julgados_LA')
        expect(f.listas.ufOpcoes).toBe('stats.julgados_uf_opcoes_LA')
        expect(sentencasFields(null).numeros.total).toBeNull()
    })

    it('lê os números, as listas e os estudos da unidade certa', () => {
        const j = lerJulgadosSentencas(RESPOSTA_RJ)
        expect(j.n.total).toBe(40)
        expect(j.n.extincaoTotalEstoque).toBe(90)
        expect(j.n.improcedenciaRevertidaEstoque).toBe(7)
        expect(j.n.semJuiz).toBe(3)
        expect(j.comparativo.total).toBe(-12.5)
        expect(j.ufOpcoes).toEqual(['RJ'])
        expect(j.ranking[0]).toMatchObject({ name: 'Dra. Fulana', procedentes: 2, improcedentes: 1, extintos: 1 })
        expect(j.extincao.estoque.porComarca[0]).toMatchObject({ name: 'Niterói', valorCausa: 100, uf: 'RJ' })
        // O motivo das extinções "entrada" é o gráfico do período, como na v1.
        expect(j.extincao.entrada.porMotivo).toEqual(j.porMotivoExtincao)
        expect(j.lista[0]).toMatchObject({ juiz: 'Dra. Fulana', status_1g: 'Procedente', data_sentenca: '2026-10-05' })
        expect(j.dadosFaltando).toEqual([{ numero_processo: '1', campo: 'Juiz' }])
    })

    it('o mock tem os nomes da rota de sentença em cada unidade', () => {
        for (const [unit, suf] of [
            ['NG', 'NG'],
            ['LA_AM', 'LA'],
            ['LA_RJ', 'RJ'],
        ]) {
            const j = lerJulgadosSentencas(julgadosSentencasFor(unit))
            expect(j.unit).toBe(suf)
            expect(j.n.total).not.toBeNull()
            expect(j.ranking.length).toBeGreaterThan(0)
            expect(j.lista.length).toBeGreaterThan(0)
        }
    })
})
