import { describe, expect, it } from 'vitest'
import { vinculacoesFor } from '../../../services/mock/vinculacoes.ts'
import { vinculacoesFilters } from './filters.ts'
import {
    doSetor,
    filtrarLista,
    lerFiltros,
    rankingProblemas,
    regraNaoCumprido,
    saudePorSetor,
    semDestino,
    totais,
    type Problema,
    type Vinculacao,
} from './vinculacoes.ts'

const base = vinculacoesFor('NG').rows ?? []
const modelo = base[0]

function vinc(id: number, parcial: Partial<Vinculacao>): Vinculacao {
    return { ...modelo, ID_VINCULACAO: id, PROBLEMAS_DETALHE: [], QTD_PROBLEMAS: 0, QTD_ERROS: 0, ...parcial }
}

const erro: Problema = { NIVEL: 'erro', TIPO: 'Encaminha para vinculação inativa', MENSAGEM: 'x' }
const falta: Problema = { NIVEL: 'incompleta', TIPO: 'Sem campos', MENSAGEM: 'y' }

const rows = [
    vinc(1, { SETOR: 'EXECUÇÃO', ATIVIDADE: 'CÁLCULO', STATUS: 'ok' }),
    vinc(2, { SETOR: 'EXECUÇÃO', ATIVIDADE: 'ALVARÁ', STATUS: 'erro', PROBLEMAS_DETALHE: [erro, erro, falta] }),
    vinc(3, { SETOR: 'RECURSOS', ATIVIDADE: 'EMBARGOS', STATUS: 'incompleta', PROBLEMAS_DETALHE: [falta] }),
    vinc(4, { SETOR: 'RECURSOS', ATIVIDADE: 'ARQUIVAR', STATUS: 'inativa' }),
]

describe('Configurações das Vinculações', () => {
    it('lê os filtros: sem status = as ativas', () => {
        expect(lerFiltros({})).toEqual({ setor: null, status: 'ativas', problema: null })
        expect(lerFiltros({ setor_vinculacao: ['RECURSOS'], status_vinculacao: ['erro'] })).toMatchObject({
            setor: 'RECURSOS',
            status: 'erro',
        })
    })

    it('conta os status e as ativas do recorte de setor', () => {
        expect(totais(rows)).toEqual({ ok: 1, incompleta: 1, erro: 1, inativa: 1, ativas: 3 })
        expect(totais(doSetor(rows, 'RECURSOS'))).toMatchObject({ ativas: 1, inativa: 1 })
    })

    it('saúde por setor: só ativas, o setor com mais erros primeiro', () => {
        expect(saudePorSetor(rows)).toEqual([
            { nome: 'EXECUÇÃO', ok: 1, incompleta: 0, erro: 1, total: 2 },
            { nome: 'RECURSOS', ok: 0, incompleta: 1, erro: 0, total: 1 },
        ])
    })

    it('ranking: cada tipo conta uma vez por vinculação, erros primeiro', () => {
        expect(rankingProblemas(rows)).toEqual([
            { tipo: 'Encaminha para vinculação inativa', nivel: 'erro', vinculacoes: 1 },
            { tipo: 'Sem campos', nivel: 'incompleta', vinculacoes: 2 },
        ])
    })

    it('lista: ativas por padrão, status, problema e busca', () => {
        const ids = (r: Vinculacao[]) => r.map((x) => x.ID_VINCULACAO)
        expect(ids(filtrarLista(rows, { status: 'ativas', problema: null }, ''))).toEqual([1, 2, 3])
        expect(ids(filtrarLista(rows, { status: 'todas', problema: null }, ''))).toEqual([1, 2, 3, 4])
        expect(ids(filtrarLista(rows, { status: 'inativa', problema: null }, ''))).toEqual([4])
        expect(ids(filtrarLista(rows, { status: 'ativas', problema: 'Sem campos' }, ''))).toEqual([2, 3])
        expect(ids(filtrarLista(rows, { status: 'ativas', problema: null }, 'embarg'))).toEqual([3])
    })

    it('regras e fluxo sem destino', () => {
        expect(regraNaoCumprido(vinc(9, { REGRA_NAO_CUMPRIDO_EXIGE_MOTIVO: false }))).toBe('não definida')
        expect(semDestino({ MODO: 'encaminha', MODO_LABEL: 'Encaminhar', DESTINOS: [] })).toBe(true)
        expect(semDestino({ MODO: 'encerra', MODO_LABEL: 'Apenas encerrar', DESTINOS: [] })).toBe(false)
    })

    it('filtros da janela: setores da resposta, status fixos e problema só pelo gráfico', () => {
        const campos = vinculacoesFilters({ meta: vinculacoesFor('NG').meta, rows })
        expect(campos.map((c) => c.key)).toEqual(['setor_vinculacao', 'status_vinculacao', 'problema_vinculacao'])
        expect(campos[0].options.map((o) => o.value)).toEqual(['EXECUÇÃO', 'RECURSOS'])
        expect(campos[2].fromChart).toBe(true)
    })

    it('o mock tem cada status e só o escritório da unidade', () => {
        const la = vinculacoesFor('LA_AM').rows ?? []
        expect(new Set(la.map((r) => r.ID_ESCRITORIO_ASSINANTE))).toEqual(new Set([21]))
        expect(new Set(base.map((r) => r.STATUS))).toEqual(new Set(['ok', 'incompleta', 'erro', 'inativa']))
    })
})
