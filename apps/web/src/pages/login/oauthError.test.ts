import { describe, expect, it } from 'vitest'
import { GENERIC_OAUTH_MESSAGE, NO_INVITE_MESSAGE, oauthErrorMessage } from './oauthError.ts'

describe('oauthErrorMessage', () => {
    it('sem erro na URL: null', () => {
        expect(oauthErrorMessage('', '')).toBeNull()
        expect(oauthErrorMessage('?code=abc&returnTo=%2Fx', '')).toBeNull()
    })

    it('hook sem convite (query, codificado): mensagem de convite', () => {
        const search = '?error=access_denied&error_code=403&error_description=Sem+convite+para+o+LexHub.'
        expect(oauthErrorMessage(search, '')).toBe(NO_INVITE_MESSAGE)
    })

    it('hook sem convite no #hash: mensagem de convite', () => {
        expect(oauthErrorMessage('', '#error=server_error&error_description=Sem%20convite%20para%20o%20LexHub.')).toBe(
            NO_INVITE_MESSAGE,
        )
    })

    it('outro erro (ex.: cancelou no Google): mensagem genérica', () => {
        expect(oauthErrorMessage('?error=access_denied&error_description=User+cancelled', '')).toBe(
            GENERIC_OAUTH_MESSAGE,
        )
    })

    it('nunca mostra o texto da URL', () => {
        const msg = oauthErrorMessage('?error=x&error_description=Sua+conta+foi+hackeada+ligue+para+0800', '')
        expect(msg).toBe(GENERIC_OAUTH_MESSAGE)
        expect(msg).not.toContain('hackeada')
    })
})
