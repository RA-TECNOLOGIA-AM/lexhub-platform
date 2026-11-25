import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMockClient } from './mockClient.ts'
import { memoryStorage } from '../lib/memoryStorage.ts'

describe('mockClient: senha do perfil', () => {
    beforeEach(() => {
        // Ambiente node: sessionStorage e localStorage falsos, em memória (o Node 24 do CI não tem).
        vi.stubGlobal('sessionStorage', memoryStorage())
        vi.stubGlobal('localStorage', memoryStorage())
        sessionStorage.setItem('lexhub.mock.session', 'x')
    })

    it('começa sem senha e passa a ter depois de criar', async () => {
        const client = createMockClient()
        expect(await client.getPasswordStatus()).toBe(false)
        await client.setPassword('abc123')
        expect(await client.getPasswordStatus()).toBe(true)
    })
})
