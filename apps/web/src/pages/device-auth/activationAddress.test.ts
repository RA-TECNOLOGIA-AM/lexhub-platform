import { describe, expect, it } from 'vitest'
import { activationAddress } from './activationAddress.ts'

describe('activationAddress', () => {
    it('tira protocolo e código do link do QR', () => {
        expect(activationAddress('https://hub.lexgroup.com.br/ativar?code=ABCD-EFGH')).toBe(
            'hub.lexgroup.com.br/ativar',
        )
    })

    it('mantém a porta (teste local)', () => {
        expect(activationAddress('http://192.168.12.231:5186/ativar?code=ABCD-EFGH')).toBe('192.168.12.231:5186/ativar')
    })

    it('link inválido não vira endereço', () => {
        expect(activationAddress('não é url')).toBeNull()
    })
})
