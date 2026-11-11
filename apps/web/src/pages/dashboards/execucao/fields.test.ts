import { describe, expect, it } from 'vitest'
import { CAMPOS, campo, nomeCampo, razao, type CampoExecucao } from './fields.ts'

const chaves = Object.keys(CAMPOS.NG) as CampoExecucao[]

describe('CAMPOS', () => {
    it('as três unidades têm as mesmas chaves', () => {
        expect(Object.keys(CAMPOS.LA).sort()).toEqual([...chaves].sort())
        expect(Object.keys(CAMPOS.RJ).sort()).toEqual([...chaves].sort())
    })
    it('LA e RJ usam o sufixo da unidade em todos os campos', () => {
        for (const u of ['LA', 'RJ'] as const) {
            for (const nome of Object.values(CAMPOS[u])) {
                if (nome !== null) expect(nome.endsWith(`_${u}`)).toBe(true)
            }
        }
    })
    it('NG: indicadores sem sufixo, atividades com _NG', () => {
        expect(CAMPOS.NG.entradas).toBe('total_em_execucao')
        expect(CAMPOS.NG.tre).toBe('tre')
        expect(CAMPOS.NG.atividadesVencidas).toBe('atividades_execucao_vencidas_NG')
    })
    it('só o LA não tem expedições de alvará cumpridas', () => {
        expect(CAMPOS.LA.alvarasCumpridos).toBeNull()
        expect(CAMPOS.NG.alvarasCumpridos).not.toBeNull()
        expect(CAMPOS.RJ.alvarasCumpridos).not.toBeNull()
    })
})

describe('campo', () => {
    it('lê o nome certo de cada unidade', () => {
        expect(campo({ estoque_inicial: 448 }, 'estoqueInicial', 'NG')).toBe(448)
        expect(campo({ estoque_inicial_LA: 1278 }, 'estoqueInicial', 'LA')).toBe(1278)
        expect(campo({ tre_RJ: 0.74 }, 'tre', 'RJ')).toBe(0.74)
    })
    it('não mistura unidades', () => {
        expect(campo({ estoque_inicial: 448 }, 'estoqueInicial', 'LA')).toBeNull()
    })
    it('null quando falta (mock com stats vazio ou sem stats)', () => {
        expect(campo({}, 'entradas', 'NG')).toBeNull()
        expect(campo(undefined, 'entradas', 'NG')).toBeNull()
        expect(campo({ total_em_execucao: null }, 'entradas', 'NG')).toBeNull()
    })
    it('null para unidade desconhecida ou indicador inexistente', () => {
        expect(nomeCampo('entradas', 'XX')).toBeNull()
        expect(campo({ cumpridas_diligencias_expedicao_alvara_execucao_LA: 3 }, 'alvarasCumpridos', 'LA')).toBeNull()
    })
})

describe('razao', () => {
    it('divide e protege contra zero/ausente', () => {
        expect(razao(100, 4)).toBe(25)
        expect(razao(100, 0)).toBeNull()
        expect(razao(null, 4)).toBeNull()
    })
})
