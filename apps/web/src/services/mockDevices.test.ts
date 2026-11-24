import { describe, expect, it } from 'vitest'
import { createMockDevices } from './mockDevices.ts'

describe('createMockDevices', () => {
    it('4 sessões, a atual primeiro', () => {
        const list = createMockDevices(() => 0).list()
        expect(list).toHaveLength(4)
        expect(list[0].current).toBe(true)
        expect(list.filter((s) => s.current)).toHaveLength(1)
    })

    it('revoke tira uma; a atual nunca sai', () => {
        const d = createMockDevices(() => 0)
        d.revoke('mock-tv')
        d.revoke('mock-atual')
        expect(d.list().map((s) => s.id)).toEqual(['mock-atual', 'mock-celular-1', 'mock-celular-2'])
    })

    it('revokeOthers deixa só a atual', () => {
        const d = createMockDevices(() => 0)
        d.revokeOthers()
        expect(d.list().map((s) => s.id)).toEqual(['mock-atual'])
    })
})
