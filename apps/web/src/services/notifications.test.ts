import { describe, expect, it } from 'vitest'
import { fakeSupabase } from './fakeSupabase.ts'
import { createNotificationsClient } from './notifications.ts'
import { createNotificationsStore } from './mock/notifications.ts'
import { bellCount } from '../lib/notifications.ts'

describe('createNotificationsClient', () => {
    it('chama as funções do schema api com os parâmetros certos', async () => {
        const { supabase, calls } = fakeSupabase({ data: { items: [], unread: 0 } })
        const client = createNotificationsClient(supabase)
        await client.listMyNotifications()
        await client.markNotificationsRead(['n1'])
        await client.markNotificationsRead(null)
        expect(calls.map((c) => c.schema)).toEqual(['api', 'api', 'api'])
        expect(calls[0]).toMatchObject({ fn: 'list_my_notifications' })
        expect(calls[1]).toMatchObject({ fn: 'mark_notifications_read', args: { p_ids: ['n1'] } })
        expect(calls[2]).toMatchObject({ fn: 'mark_notifications_read', args: { p_ids: null } })
    })
})

describe('createNotificationsStore (mock)', () => {
    const base = { kind: 'access_request.approved' as const, title: 'Seu acesso foi aprovado', body: null, link: null }

    it('cada pessoa vê só as próprias, mais recentes primeiro', () => {
        const store = createNotificationsStore()
        store.add('a@x.com', { ...base, title: 'primeira' })
        store.add('a@x.com', { ...base, title: 'segunda' })
        store.add('b@x.com', base)
        const a = store.list('a@x.com')
        expect(a.unread).toBe(2)
        expect(a.items.map((n) => n.title)).toEqual(['segunda', 'primeira'])
        expect(store.list('c@x.com')).toEqual({ items: [], unread: 0 })
    })

    it('marca uma ou todas como lidas', () => {
        const store = createNotificationsStore()
        store.add('a@x.com', base)
        store.add('a@x.com', base)
        const [first] = store.list('a@x.com').items
        store.markRead('a@x.com', [first.id])
        expect(store.list('a@x.com').unread).toBe(1)
        store.markRead('a@x.com', null)
        expect(store.list('a@x.com').unread).toBe(0)
    })
})

describe('bellCount', () => {
    it('soma não lidas e pedidos; nada = sem número; acima de 9 = 9+', () => {
        expect(bellCount(0, 0)).toBeNull()
        expect(bellCount(1, 2)).toBe('3')
        expect(bellCount(8, 4)).toBe('9+')
    })
})
