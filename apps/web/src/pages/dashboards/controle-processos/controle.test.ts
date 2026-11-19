import { describe, expect, it } from 'vitest'
import { duracao, filtrosControle, lerControle, tempoProtocolo, type ControleResponse } from './controle.ts'

const meta = { unit: 'NG', from: '2026-11-01', to: '2026-11-19', source: 'LexFlow', synced_at: null, timezone: 'x' }
const c = (k: string) => `controle_processo_${k}_NG`

const resposta = (extra: Partial<ControleResponse> = {}): ControleResponse => ({
    meta,
    unidade: 'NG',
    periodo: {
        [c('extintos_com_merito_qtd')]: 10,
        [c('extintos_sem_merito_qtd')]: 4,
        [c('extintos_sem_merito_valor_causa')]: 1000,
        [c('extintos_com_merito_2g_qtd')]: 3,
        [c('extintos_sem_merito_2g_qtd')]: 1,
        [c('extintos_sem_merito_2g_valor_causa')]: 500,
        [c('extintos_com_merito_por_tipo_sentenca')]: [
            { tipo_sentenca: 'SENTENÇA B', quantidade: 2 },
            { tipo_sentenca: 'SENTENÇA A', quantidade: 8, valor_causa: 50 },
        ],
    },
    historico: {
        total_controle_processo_NG: 100,
        [c('fase_inicial_qtd')]: 60,
        [c('por_fase')]: [
            { name: 'RECURSAL', value: 30 },
            { name: 'INICIAL', value: 60 },
        ],
        [c('uf_opcoes')]: ['AM', 'PA'],
    },
    protocolo: { protocolos_resolvidos: 5, valor_causa_protocolo_novo: 2000 },
    lexpre: { protocolados_total: 7, valor_causa_protocolado: 8000 },
    execucao: {
        total_saida_execucao_periodo: 3,
        valor_ted_saida_execucao_periodo: 300,
        total_saida_execucao_acordos_periodo_NG: 2,
        valor_ted_saida_execucao_acordos_periodo_NG: 200,
        total_em_execucao: 40,
        valor_total_em_execucao: 4000,
        total_em_execucao_acordos_NG: 10,
        valor_total_em_execucao_acordos_NG: 1000,
    },
    ...extra,
})

describe('lerControle (as somas da v1)', () => {
    it('protocolados = legado + LexPre; execução = condenação + acordos; arquivados = saídas, TED da condenação', () => {
        const x = lerControle(resposta())
        expect(x.protocolados).toEqual({ qtd: 12, valor: 10000 })
        expect(x.execucao).toEqual({ qtd: 50, valor: 5000 })
        expect(x.arquivadosProcedencia).toEqual({ qtd: 5, valor: 300 })
        expect(x.total.qtd).toBe(100)
        expect(x.inicial.qtd).toBe(60)
    })

    it('extintos, carteira líquida e listas por tipo (maior primeiro)', () => {
        const x = lerControle(resposta())
        expect([x.extintos1g.total, x.extintos2g.total, x.totalExtintos]).toEqual([14, 4, 18])
        expect(x.carteiraLiquida).toBe(10000 - 1000 - 500)
        expect(x.extintos1g.porTipo.map((t) => t.tipo)).toEqual(['SENTENÇA A', 'SENTENÇA B'])
    })

    it('"suspenso" zera protocolados e execução (sempre ativos, como a v1)', () => {
        const x = lerControle(resposta(), { situacao_controle: ['suspenso'] })
        expect(x.situacao).toBe('suspenso')
        expect(x.protocolados).toEqual({ qtd: 0, valor: 0 })
        expect(x.execucao).toEqual({ qtd: 0, valor: 0 })
        expect(x.arquivadosProcedencia.qtd).toBe(5)
    })

    it('fases maior primeiro; subfases só com fase', () => {
        expect(lerControle(resposta()).fases).toEqual(['INICIAL', 'RECURSAL'])
        expect(lerControle(resposta()).subfases).toBeNull()
        const x = lerControle(
            resposta({
                fase: {
                    [c('por_subfase')]: [
                        { name: 'B', value: 1 },
                        { name: 'A', value: 5, tempo_medio_dias: 2 },
                    ],
                    [c('total_na_fase')]: 6,
                },
            }),
        )
        expect(x.subfases?.itens.map((s) => s.name)).toEqual(['A', 'B'])
        expect(x.subfases?.total).toBe(6)
    })
})

describe('tempo até o protocolo (legado + LexPre)', () => {
    const legado = (n: number) => ({
        protocolos_resolvidos: n,
        tempo_medio_contratacao_protocolo: 10,
        mediana_tempo_contratacao_protocolo: 8,
        comparativo_tempo_medio_contratacao_protocolo: 5,
    })
    const lexpre = (n: number) => ({
        protocolados_total: n,
        media_tempo_protocolado: 1,
        mediana_tempo_protocolado: 0.5,
        comparativo_tempo_medio_protocolado: -20,
    })
    it('só LexPre (hoje): o tempo do LexPre', () => {
        const t = tempoProtocolo(legado(0), lexpre(30))
        expect(t.fonte).toBe('lexpre')
        expect(t.media).toEqual({ valor: 1, comparativo: -20 })
        expect(t.mediana.valor).toBe(0.5)
    })
    it('só legado: o tempo da v1', () => {
        expect(tempoProtocolo(legado(3), lexpre(0))).toMatchObject({ fonte: 'legado', media: { valor: 10 } })
    })
    it('os dois: média ponderada; mediana e variação de quem teve mais', () => {
        const t = tempoProtocolo(legado(10), lexpre(30))
        expect(t.fonte).toBe('ambos')
        expect(t.media.valor).toBeCloseTo((10 * 10 + 1 * 30) / 40)
        expect(t.media.comparativo).toBe(-20)
        expect(t.mediana.valor).toBe(0.5)
    })
    it('nenhum: sem valor (e não 0h / -100%)', () => {
        const t = tempoProtocolo(legado(0), lexpre(0))
        expect(t.fonte).toBeNull()
        expect(t.media).toEqual({ valor: null, comparativo: null })
    })
})

describe('duracao (formatPermanenciaFromDays da v1)', () => {
    it('dias e horas', () => {
        expect(duracao(null)).toBe('—')
        expect(duracao(0)).toBe('0h')
        expect(duracao(0.25)).toBe('6h')
        expect(duracao(204.48)).toBe('204d 11h')
        expect(duracao(12)).toBe('12d')
    })
})

describe('filtros', () => {
    it('situação (uma), UFs e a fase (no gráfico, fora da janela)', () => {
        const f = filtrosControle(resposta())
        expect(f.map((x) => [x.key, !!x.single, !!x.inline])).toEqual([
            ['situacao_controle', true, false],
            ['uf_controle', false, false],
            ['fase_controle', true, true],
        ])
        expect(filtrosControle({ meta })).toEqual([])
    })
})
