import { describe, expect, it } from 'vitest'
import { deviceKind, groupSessions } from './devices.ts'
import type { AccountSession } from '../../types/index.ts'

const WIN = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0 Safari/537.36'
const AND = 'Mozilla/5.0 (Linux; Android 14) Chrome/131.0 Mobile Safari/537.36'
const s = (id: string, over: Partial<AccountSession> = {}): AccountSession => ({
    id,
    createdAt: '2026-11-20T10:00:00Z',
    lastActiveAt: '2026-11-24T10:00:00Z',
    userAgent: WIN,
    ip: '10.0.0.1',
    current: false,
    ...over,
})

describe('deviceKind', () => {
    it('TV pelo QR, celular por Android/iOS, o resto computador', () => {
        expect(deviceKind('python-httpx/0.27.0')).toBe('tv')
        expect(deviceKind(AND)).toBe('phone')
        expect(deviceKind('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Safari/604.1')).toBe('phone')
        expect(deviceKind(WIN)).toBe('computer')
        expect(deviceKind(null)).toBe('computer')
    })
})

describe('groupSessions', () => {
    it('a atual vem primeiro e sozinha, mesmo com outra igual', () => {
        const g = groupSessions([s('b'), s('a', { current: true })])
        expect(g.map((x) => [x.ids, x.current])).toEqual([
            [['a'], true],
            [['b'], false],
        ])
    })

    it('mesmo IP e navegador = um grupo; vale a última atividade', () => {
        const g = groupSessions([
            s('p1', { userAgent: AND, ip: '177.1.1.1', lastActiveAt: '2026-11-24T09:00:00Z' }),
            s('p2', { userAgent: AND, ip: '177.1.1.1', lastActiveAt: '2026-11-24T11:00:00Z' }),
            s('w', { ip: '177.1.1.1', lastActiveAt: '2026-11-24T10:00:00Z' }),
        ])
        expect(g).toHaveLength(2)
        expect(g[0]).toMatchObject({
            ids: ['p1', 'p2'],
            label: 'Chrome · Android',
            kind: 'phone',
            ip: '177.1.1.1',
            lastActiveAt: '2026-11-24T11:00:00Z',
        })
        expect(g[1].ids).toEqual(['w'])
    })

    it('navegador desconhecido: "Aparelho desconhecido"', () => {
        expect(groupSessions([s('x', { userAgent: null })])[0].label).toBe('Aparelho desconhecido')
    })
})
