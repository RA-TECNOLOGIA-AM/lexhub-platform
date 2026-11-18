import { describe, expect, it } from 'vitest'
import type { SourcesResponse } from '../../types/index.ts'
import { DataError } from '../errors.ts'
import { catalog } from './catalog.ts'
import { connectIn, disconnectIn, requireSourceOn, setEnabledIn } from './connections.ts'
import { sourceDetailFor } from './sourceDetail.ts'
import { sources } from './sources.ts'

const fresh = (): SourcesResponse => structuredClone(sources)

describe('ligar/desligar fonte no mock (mesmas regras da API)', () => {
    it('desligar: status Desligada, o dashboard da planilha responde 423; religar volta sem novo link', () => {
        const data = fresh()
        expect(setEnabledIn(data, 'sheets_financeiro_ng', false).status).toBe('disabled')
        const detail = sourceDetailFor(data, catalog, 'NG', 'sheets_financeiro_ng')!
        expect(detail.enabled).toBe(false)
        expect(() => requireSourceOn('meta-anual', 'NG')).toThrowError(
            expect.objectContaining({ status: 423 }) as DataError,
        )
        expect(() => requireSourceOn('meta-anual', 'LA_AM')).not.toThrow() // a LA segue ligada

        expect(setEnabledIn(data, 'sheets_financeiro_ng', true).status).toBe('late') // o status de antes
        expect(() => requireSourceOn('meta-anual', 'NG')).not.toThrow()
    })

    it('planilha antiga (inteira) não desconecta: desliga-se', () => {
        expect(() => disconnectIn(fresh(), 'sheets_financeiro_la')).toThrowError(/desligue em vez de desconectar/)
    })

    it('produto Lex e banco interno não ligam/desligam pela tela', () => {
        expect(() => setEnabledIn(fresh(), 'lexpre', false)).toThrowError(/não é gerenciada pela tela/)
        expect(() => setEnabledIn(fresh(), 'ng', false)).toThrowError(/não é gerenciada pela tela/)
    })

    it('detalhe técnico: a chave e a estrutura salva no teste; nunca o segredo', () => {
        const data = fresh()
        const res = connectIn(data, 'NG', {
            connector: 'postgres',
            name: 'Banco NG',
            host: 'db.operacao.com.br',
            port: null,
            database: 'operacao',
            user: 'lexhub_leitura',
            password: 's3nh@',
            ssl: true,
            writerAck: false,
        })
        const detail = sourceDetailFor(data, catalog, 'NG', res.source!.id)!
        expect(detail.technical?.key).toBe(res.source!.id)
        expect(Object.keys(detail.technical?.schema ?? {})).toContain('public.processo')
        expect(JSON.stringify(detail)).not.toContain('s3nh@')
    })
})
