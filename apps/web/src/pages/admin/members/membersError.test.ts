import { describe, expect, it } from 'vitest'
import { DataError } from '../../../services/errors.ts'
import { membersErrorView } from './membersError.ts'

describe('membersErrorView', () => {
    it('403 do banco: quem abriu não gere membros (estado próprio, não a tela de erro)', () => {
        expect(membersErrorView(new DataError(403, 'Você não gere membros nesta organização.'))).toEqual({
            forbidden: true,
        })
    })
    it('outros erros seguem para a tela de erro comum', () => {
        expect(membersErrorView(new DataError(0, 'Sem conexão'))).toEqual({ forbidden: false })
        expect(membersErrorView(new Error('x'))).toEqual({ forbidden: false })
    })
})
