import { describe, expect, it } from 'vitest'
import { withCatalogCache } from './catalogCache.ts'
import type { DataClient } from './client.ts'
import type { DashboardCatalog } from '../types/index.ts'

const catalog = (key: string): DashboardCatalog => ({
    available: [
        {
            key,
            title: key,
            area: 'Operação jurídica',
            desc: '',
            units: ['NG'],
            source: 'LexPre',
            synced_at: null,
            max_delay_min: 60,
            can_export: true,
            can_see_commission: false,
        },
    ],
    upcoming: [],
})

// DataClient falso: conta as buscas do catálogo; fail = a próxima busca falha.
function fakeClient() {
    const state = { calls: 0, fail: false }
    const client = {
        async listDashboards(org: string) {
            state.calls += 1
            if (state.fail) throw new Error('API fora do ar')
            return catalog(`${org}-${state.calls}`)
        },
        async signIn() {},
        async signOut() {},
    } as unknown as DataClient
    return { client, state }
}

describe('withCatalogCache', () => {
    it('busca uma vez e devolve o mesmo catálogo enquanto vale', async () => {
        const { client, state } = fakeClient()
        const cached = withCatalogCache(client, 1000, () => 0)
        const a = await cached.listDashboards('lexgroup')
        const b = await cached.listDashboards('lexgroup')
        expect(state.calls).toBe(1)
        expect(b).toBe(a)
    })

    it('cada organização tem o seu', async () => {
        const { client, state } = fakeClient()
        const cached = withCatalogCache(client, 1000, () => 0)
        await cached.listDashboards('lexgroup')
        await cached.listDashboards('cliente-parceiro')
        expect(state.calls).toBe(2)
    })

    it('passado o prazo, busca de novo', async () => {
        const { client, state } = fakeClient()
        let t = 0
        const cached = withCatalogCache(client, 1000, () => t)
        await cached.listDashboards('lexgroup')
        t = 1000
        await cached.listDashboards('lexgroup')
        expect(state.calls).toBe(2)
    })

    it('erro não fica guardado', async () => {
        const { client, state } = fakeClient()
        const cached = withCatalogCache(client, 1000, () => 0)
        state.fail = true
        await expect(cached.listDashboards('lexgroup')).rejects.toThrow('API fora do ar')
        state.fail = false
        await expect(cached.listDashboards('lexgroup')).resolves.toBeTruthy()
        expect(state.calls).toBe(2)
    })

    it('sair e entrar limpam o cache', async () => {
        const { client, state } = fakeClient()
        const cached = withCatalogCache(client, 1000, () => 0)
        await cached.listDashboards('lexgroup')
        await cached.signOut()
        await cached.listDashboards('lexgroup')
        await cached.signIn('a@b.com', 'x')
        await cached.listDashboards('lexgroup')
        expect(state.calls).toBe(3)
    })
})
