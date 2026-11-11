import { describe, expect, it } from 'vitest'
import { withSessionCache } from './sessionCache.ts'
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

// DataClient falso: conta as buscas por método; fail = a próxima busca falha; guarda as escritas.
function fakeClient() {
    const state = {
        calls: { catalog: 0, favorites: 0, order: 0 },
        fail: false,
        failWrite: false,
        favorites: ['protocolo-lexpre'],
        order: ['a', 'b'],
    }
    const client = {
        async listDashboards(org: string) {
            state.calls.catalog += 1
            if (state.fail) throw new Error('API fora do ar')
            return catalog(`${org}-${state.calls.catalog}`)
        },
        async listFavorites() {
            state.calls.favorites += 1
            return [...state.favorites]
        },
        async getHubOrder() {
            state.calls.order += 1
            return [...state.order]
        },
        async setFavorite(_org: string, key: string, favorite: boolean) {
            if (state.failWrite) throw new Error('falhou')
            state.favorites = favorite ? [...state.favorites, key] : state.favorites.filter((k) => k !== key)
        },
        async setHubOrder(_org: string, keys: string[]) {
            state.order = keys
        },
        async signIn() {},
        async signInWithGoogle() {
            return 'signed-in'
        },
        async signOut() {},
    } as unknown as DataClient
    return { client, state }
}

describe('withSessionCache', () => {
    it('catálogo, favoritos e ordem: uma busca enquanto vale', async () => {
        const { client, state } = fakeClient()
        const cached = withSessionCache(client, 1000, () => 0)
        for (let i = 0; i < 3; i++) {
            await cached.listDashboards('lexgroup')
            await cached.listFavorites('lexgroup')
            await cached.getHubOrder('lexgroup')
        }
        expect(state.calls).toEqual({ catalog: 1, favorites: 1, order: 1 })
    })

    it('cada organização tem o seu', async () => {
        const { client, state } = fakeClient()
        const cached = withSessionCache(client, 1000, () => 0)
        await cached.listDashboards('lexgroup')
        await cached.listDashboards('cliente-parceiro')
        expect(state.calls.catalog).toBe(2)
    })

    it('passado o prazo, busca de novo', async () => {
        const { client, state } = fakeClient()
        let t = 0
        const cached = withSessionCache(client, 1000, () => t)
        await cached.listDashboards('lexgroup')
        t = 1000
        await cached.listDashboards('lexgroup')
        expect(state.calls.catalog).toBe(2)
    })

    it('erro não fica guardado', async () => {
        const { client, state } = fakeClient()
        const cached = withSessionCache(client, 1000, () => 0)
        state.fail = true
        await expect(cached.listDashboards('lexgroup')).rejects.toThrow('API fora do ar')
        state.fail = false
        await expect(cached.listDashboards('lexgroup')).resolves.toBeTruthy()
        expect(state.calls.catalog).toBe(2)
    })

    it('favoritar atualiza o guardado sem buscar de novo', async () => {
        const { client, state } = fakeClient()
        const cached = withSessionCache(client, 1000, () => 0)
        await cached.listFavorites('lexgroup')
        await cached.setFavorite('lexgroup', 'pendencias-lexpre', true)
        expect(await cached.listFavorites('lexgroup')).toEqual(['protocolo-lexpre', 'pendencias-lexpre'])
        await cached.setFavorite('lexgroup', 'protocolo-lexpre', false)
        expect(await cached.listFavorites('lexgroup')).toEqual(['pendencias-lexpre'])
        expect(state.calls.favorites).toBe(1)
    })

    it('favoritar que falhou não muda o guardado', async () => {
        const { client, state } = fakeClient()
        const cached = withSessionCache(client, 1000, () => 0)
        await cached.listFavorites('lexgroup')
        state.failWrite = true
        await expect(cached.setFavorite('lexgroup', 'x', true)).rejects.toThrow()
        expect(await cached.listFavorites('lexgroup')).toEqual(['protocolo-lexpre'])
    })

    it('arrastar salva a ordem e o guardado já é a nova', async () => {
        const { client, state } = fakeClient()
        const cached = withSessionCache(client, 1000, () => 0)
        await cached.getHubOrder('lexgroup')
        await cached.setHubOrder('lexgroup', ['b', 'a'])
        expect(await cached.getHubOrder('lexgroup')).toEqual(['b', 'a'])
        expect(state.calls.order).toBe(1)
    })

    it('sair e entrar limpam tudo', async () => {
        const { client, state } = fakeClient()
        const cached = withSessionCache(client, 1000, () => 0)
        await cached.listDashboards('lexgroup')
        await cached.listFavorites('lexgroup')
        await cached.signOut()
        await cached.listDashboards('lexgroup')
        await cached.listFavorites('lexgroup')
        await cached.signIn('a@b.com', 'x')
        await cached.listDashboards('lexgroup')
        expect(state.calls.catalog).toBe(3)
        expect(state.calls.favorites).toBe(2)
    })

    it('entrar com o Google também limpa tudo', async () => {
        const { client, state } = fakeClient()
        const cached = withSessionCache(client, 1000, () => 0)
        await cached.listDashboards('lexgroup')
        await cached.signInWithGoogle()
        await cached.listDashboards('lexgroup')
        expect(state.calls.catalog).toBe(2)
    })
})
