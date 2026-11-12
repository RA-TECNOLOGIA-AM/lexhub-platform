import { describe, expect, it } from 'vitest'
import { DataError } from '../../../services/errors.ts'
import { accessErrorView } from './accessError.ts'

describe('accessErrorView', () => {
    it('403 do banco: quem abriu não gere acesso (matriz + aviso, não a tela de erro)', () => {
        expect(accessErrorView(new DataError(403, 'Você não gere acesso nesta organização.'))).toEqual({
            forbidden: true,
        })
    })
    it('outros erros seguem para a tela de erro comum', () => {
        expect(accessErrorView(new DataError(0, 'Sem conexão'))).toEqual({ forbidden: false })
    })
})
