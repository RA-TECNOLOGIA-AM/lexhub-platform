import { describe, expect, it } from 'vitest'
import {
    SELECAO_VAZIA,
    agruparPorVolume,
    alternar,
    aplicarFiltros,
    decodificar,
    formatarPValor,
    medianaSimples,
    obsEstagio2,
    ranking,
    obsEstagio1,
    resumo,
    type SobrevivenciaResponse,
} from './sobrevivencia.ts'
import { sobrevivenciaFor } from '../../../services/mock/sobrevivencia.ts'

const meta = { unit: 'NG' } as unknown as SobrevivenciaResponse['meta']
const payload: SobrevivenciaResponse = {
    meta,
    escritorio_dict: ['NG', 'LA'],
    tipo_acao_dict: ['PROCEDIMENTO COMUM', 'AGRAVO INTERNO'],
    materia_dict: ['CESTA', 'RMC'],
    tipo_evento_e1_dict: [
        'CENSURADO',
        'ACORDO',
        'MERITO_FAVORAVEL_COM_PROVEITO',
        'MERITO_SEM_PROVEITO_OU_DESFAVORAVEL',
    ],
    tipo_evento_e2_dict: ['PAGO', 'CENSURADO_PAGAMENTO'],
    tipo_acordo_dict: ['PRE_SENTENCA', 'POS_SENTENCA'],
    registros: {
        escritorio: [0, 1, 0],
        duracao_e1: [100, 200, 300],
        evento_e1: [1, 1, 0],
        tipo_evento_e1: [2, 1, 0],
        tipo_acordo: [null, 0, null],
        duracao_acordo: [null, 190, null],
        tipo_acao: [0, 1, null],
        materia: [0, 1, 0],
        tipo_evento_e2: [0, 1, null],
        duracao_e2: [40, 80, null],
        evento_sentenca: [1, 0, 0],
        sentenca_favoravel: [1, 0, 0],
        duracao_sentenca: [90, 200, 300],
        evento_acordao: [0, 0, 0],
        acordao_favoravel: [0, 0, 0],
        duracao_acordao: [100, 200, 300],
    },
}

describe('coorte e filtros', () => {
    const linhas = decodificar(payload)
    it('decodifica as colunas; agravo e mandado de segurança ficam sem tipo de ação', () => {
        expect(linhas).toHaveLength(3)
        expect(linhas[0]).toMatchObject({
            escritorio: 'NG',
            tipoEvento1: 'MERITO_FAVORAVEL_COM_PROVEITO',
            materia: 'CESTA',
            tipoAcao: 'PROCEDIMENTO COMUM',
        })
        expect(linhas[1].tipoAcao).toBeNull()
        expect(linhas[1].tipoAcordo).toBe('PRE_SENTENCA')
        expect(linhas[0].sentencaImprocedente).toBe(0) // coluna ausente no payload antigo
    })
    it('OU dentro do campo, E entre campos, e o gráfico sem o próprio filtro', () => {
        const sel = alternar(alternar(SELECAO_VAZIA, 'materia', 'CESTA'), 'materia', 'RMC')
        expect(aplicarFiltros(linhas, sel)).toHaveLength(3)
        const comTipo = alternar(sel, 'tipoAcao', 'PROCEDIMENTO COMUM')
        expect(aplicarFiltros(linhas, comTipo)).toHaveLength(1)
        expect(aplicarFiltros(linhas, comTipo, 'tipoAcao')).toHaveLength(3)
        expect(alternar(sel, 'materia', 'RMC').materia).toEqual(['CESTA'])
    })
    it('Estágio 2: só elegíveis; evento = pago', () => {
        expect(obsEstagio2(linhas)).toEqual([
            { duracao: 40, evento: 1 },
            { duracao: 80, evento: 0 },
        ])
    })
    it('resumo: % sobre a coorte, mediana do acordo direta e taxa de pagamento', () => {
        const r = resumo(linhas)
        expect(r.coorte).toBe(3)
        expect(r.pctMeritoFavoravel).toBe(33.3)
        expect(r.acordoPre).toEqual({ pct: 33.3, mediana: 190 })
        expect(r.sentenca.favoravel).toBe(100)
        expect(r.estagio2).toMatchObject({ elegiveis: 2, pagos: 1, taxa: 50 })
    })
})

describe('rankings e formatação', () => {
    it('agrupa com mínimo e top-N; ranking pela mediana, mais lento primeiro, com log-rank', () => {
        const linhas = decodificar(sobrevivenciaFor('NG'))
        const grupos = agruparPorVolume(linhas, 'materia')
        expect(grupos.every((g) => g.linhas.length >= 30)).toBe(true)
        const r = ranking(grupos, obsEstagio1)
        expect(r.itens.map((i) => i.value)).toEqual([...r.itens.map((i) => i.value)].sort((a, b) => b - a))
        expect(r.logRank?.df).toBe(grupos.length - 1)
        expect(agruparPorVolume(linhas, 'materia', 30, 2)).toHaveLength(2)
    })
    it('mediana simples, p-valor como a v1 e mock só na NG', () => {
        expect(medianaSimples([3, 1, 2])).toBe(2)
        expect(medianaSimples([1, 2, 3, 4])).toBe(3)
        expect(medianaSimples([])).toBeNull()
        expect(formatarPValor(0.03214)).toBe('p = 0,0321')
        expect(formatarPValor(0.00001)).toBe('p < 0,0001')
        expect(sobrevivenciaFor('LA_RJ').registros).toBeUndefined()
        expect(sobrevivenciaFor('LA_AM').escritorio_dict).toEqual(['LA'])
    })
})
