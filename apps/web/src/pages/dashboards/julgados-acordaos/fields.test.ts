import { describe, expect, it } from 'vitest'
import { julgadosAcordaosFor } from '../../../services/mock/julgadosAcordaos.ts'
import {
    COMPARAVEIS,
    JULGADOS_LISTAS,
    JULGADOS_NUMEROS,
    julgadosFields,
    lerJulgadosAcordaos,
    unidadeJulgados,
} from './fields.ts'
import type { JulgadosAcordaosResponse } from './types.ts'

const meta = (unit: string) => ({
    unit,
    from: '2026-10-01',
    to: '2026-10-31',
    source: 'LexFlow',
    synced_at: null,
    timezone: 'America/Manaus',
})

// Trecho no formato da DashboardResponse da v1 (model_dump): a resposta traz também os campos das outras
// unidades, vazios.
const RESPOSTA_LA: JulgadosAcordaosResponse = {
    meta: meta('LA'),
    dashboard: 'julgados_acordaos_LA',
    stats: {
        julgados_acordao_total_LA: 40,
        julgados_acordao_procedentes_LA: 20,
        julgados_acordao_improcedentes_LA: 12,
        julgados_acordao_extintos_LA: 6,
        julgados_acordao_nao_classificados_LA: 2,
        julgados_acordao_tempo_medio_dias_LA: 210.4,
        julgados_acordao_valor_fixado_procedentes_LA: 123456.78,
        comparativo_julgados_acordao_total_LA: -12.5,
        comparativo_julgados_acordao_valor_fixado_procedentes_LA: null,
        julgados_acordao_uf_opcoes_LA: ['am', 'AM '],
        julgados_comarca_opcoes_LA: ['Manaus', 'Parintins'],
        julgados_acordao_sem_relator_LA: 3,
        julgados_acordao_dados_faltando_LA: [{ numero_processo: '0600000102024804001', campo: 'Relator' }],
        julgados_acordao_total_NG: 999, // de outra unidade: não pode ser lido
    },
    ranking_relatores_acordao_julgados_LA: [
        {
            name: 'Roberta Sales',
            initials: 'RS',
            total_casos: 4,
            taxa_sucesso: 50,
            fav: 2,
            des: 1,
            outros: 1,
            percent_fav: 50,
            percent_des: 25,
            percent_outros: 25,
        },
    ],
    julgados_acordao_por_materia_LA: [
        { name: 'ANP', value: 30 },
        { name: ' ', value: 1 }, // sem nome: fora
    ],
    historico_julgados_acordao_por_materia_LA: [{ name: 'MORA', value: 3 }],
    julgados_acordao_improcedencia_por_comarca_estoque_LA: [
        { name: 'Manaus', value: 5, valor_causa: 1000, uf: 'am', tempo_medio_dias: 200 },
    ],
    julgados_acordao_procedentes_por_mes_LA: [{ name: 'out 2026', value: 20 }],
    julgados_acordao_lista_LA: [
        {
            id: 1,
            numero_processo: '06000001020248040012',
            fase: 'Recursal',
            subfase: 'Arquivado',
            status_2g: 'Procedente',
            uf: 'AM',
            relator: 'Roberta Sales',
            data_acordao: '2026-10-05',
            status_acordao_embargos: '',
            data_acordao_embargos: null,
        },
    ],
    julgados_acordao_por_materia_NG: [{ name: 'NÃO É DA LA', value: 1 }],
}

describe('julgadosFields: o campo certo de cada unidade', () => {
    it('NG: tudo com _NG, inclusive os recursos ao STJ/STF', () => {
        const f = julgadosFields('NG')
        for (const k of JULGADOS_NUMEROS) expect(f.numeros[k]).toMatch(/_NG$/)
        expect(f.numeros.total).toBe('julgados_acordao_total_NG')
        expect(f.numeros.valorFixado).toBe('julgados_acordao_valor_fixado_procedentes_NG')
        expect(f.numeros.improcedenciaStjEstoque).toBe('julgados_acordao_improcedencia_stj_estoque_NG')
        expect(f.comparativos.tempoMedio).toBe('comparativo_julgados_acordao_tempo_medio_dias_NG')
        expect(f.listas.ranking).toBe('ranking_relatores_acordao_julgados_NG')
        expect(f.listas.historicoPorMateria).toBe('historico_julgados_acordao_por_materia_NG')
        expect(f.listas.ufOpcoes).toBe('stats.julgados_acordao_uf_opcoes_NG')
        expect(f.listas.comarcaOpcoes).toBe('stats.julgados_comarca_opcoes_NG')
    })

    it('LA e RJ: sufixo da unidade; STJ/STF não existem', () => {
        for (const unit of ['LA', 'RJ'] as const) {
            const f = julgadosFields(unit)
            expect(f.numeros.procedentes).toBe(`julgados_acordao_procedentes_${unit}`)
            expect(f.comparativos.revertidos).toBe(`comparativo_julgados_acordao_revertidos_${unit}`)
            expect(f.listas.lista).toBe(`julgados_acordao_lista_${unit}`)
            expect(f.listas.improcedenciaPorRelatorEstoque).toBe(
                `julgados_acordao_improcedencia_por_relator_estoque_${unit}`,
            )
            expect(f.numeros.improcedenciaStj).toBeNull()
            expect(f.numeros.improcedenciaStfEstoque).toBeNull()
        }
    })

    it('unidade desconhecida: nenhum campo', () => {
        const f = julgadosFields(null)
        for (const k of JULGADOS_NUMEROS) expect(f.numeros[k]).toBeNull()
        for (const k of COMPARAVEIS) expect(f.comparativos[k]).toBeNull()
        for (const k of JULGADOS_LISTAS) expect(f.listas[k]).toBeNull()
    })
})

describe('unidadeJulgados', () => {
    it('pelo nome da rota da v1 e, sem ele, pelo código da unidade', () => {
        expect(unidadeJulgados({ meta: meta('LA_RJ'), dashboard: 'julgados_acordaos_RJ' })).toBe('RJ')
        expect(unidadeJulgados({ meta: meta('NG') })).toBe('NG')
        expect(unidadeJulgados({ meta: meta('Consolidado') })).toBeNull()
        expect(unidadeJulgados({ meta: meta('NG'), dashboard: 'outro' })).toBe('NG')
    })
})

describe('lerJulgadosAcordaos', () => {
    it('lê só os campos da unidade da resposta', () => {
        const j = lerJulgadosAcordaos(RESPOSTA_LA)
        expect(j.unit).toBe('LA')
        expect(j.n.total).toBe(40)
        expect(j.n.tempoMedio).toBe(210.4)
        expect(j.n.valorFixado).toBe(123456.78)
        expect(j.n.embargados).toBeNull() // ausente
        expect(j.n.improcedenciaStj).toBeNull() // não existe na LA
        expect(j.comparativo.total).toBe(-12.5)
        expect(j.comparativo.valorFixado).toBeNull()
        expect(j.ufOpcoes).toEqual(['AM', 'AM'])
        expect(j.comarcaOpcoes).toEqual(['Manaus', 'Parintins'])
        expect(j.dadosFaltando).toEqual([{ numero_processo: '0600000102024804001', campo: 'Relator' }])
        expect(j.porMateria.map((p) => p.name)).toEqual(['ANP'])
        expect(j.historicoPorMateria.map((p) => p.name)).toEqual(['MORA'])
        expect(j.ranking[0]).toMatchObject({ name: 'Roberta Sales', total: 4, procedentes: 2, pctExtintos: 25 })
        expect(j.improcedencia.estoque.porComarca[0]).toEqual({
            name: 'Manaus',
            value: 5,
            valorCausa: 1000,
            uf: 'AM',
            tempoMedioDias: 200,
        })
        expect(j.improcedencia.entrada.porComarca).toEqual([])
        expect(j.porMes.procedentes).toHaveLength(1)
        expect(j.lista[0]).toMatchObject({
            relator: 'Roberta Sales',
            data_acordao: '2026-10-05',
            data_acordao_embargos: null,
        })
    })

    it('resposta vazia (só meta e stats {}): tudo null ou vazio, sem quebrar', () => {
        const j = lerJulgadosAcordaos({ meta: meta('NG'), stats: {} })
        expect(j.unit).toBe('NG')
        for (const k of JULGADOS_NUMEROS) expect(j.n[k]).toBeNull()
        expect(j.ranking).toEqual([])
        expect(j.lista).toEqual([])
    })

    it('o mock tem todos os campos que a tela lê, nas três unidades', () => {
        for (const [unit, suf] of [
            ['NG', 'NG'],
            ['LA_AM', 'LA'],
            ['LA_RJ', 'RJ'],
        ]) {
            const j = lerJulgadosAcordaos(julgadosAcordaosFor(unit))
            expect(j.unit).toBe(suf)
            const faltando = JULGADOS_NUMEROS.filter((k) => j.n[k] === null)
            expect(faltando).toEqual(
                suf === 'NG'
                    ? []
                    : ['improcedenciaStj', 'improcedenciaStf', 'improcedenciaStjEstoque', 'improcedenciaStfEstoque'],
            )
            expect(j.lista.length).toBeGreaterThan(0)
            expect(j.lista).toHaveLength(j.n.total ?? -1)
            expect(j.ranking.length).toBeGreaterThan(0)
            expect(j.porMes.procedentes.length).toBeGreaterThan(12)
        }
    })
})
