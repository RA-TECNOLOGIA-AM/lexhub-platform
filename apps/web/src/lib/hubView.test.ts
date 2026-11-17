import { describe, expect, it } from 'vitest'
import { areaColor, HUB_VIEW_KEY, storedHubView, storeHubView } from './hubView.ts'

function memory(initial: Record<string, string> = {}) {
    const data = { ...initial }
    return {
        data,
        getItem: (k: string) => data[k] ?? null,
        setItem: (k: string, v: string) => {
            data[k] = v
        },
    }
}

describe('hubView', () => {
    it('lê a escolha guardada; sem escolha, valor estranho ou storage quebrado = lista', () => {
        expect(storedHubView(memory({ [HUB_VIEW_KEY]: 'quadro' }))).toBe('quadro')
        expect(storedHubView(memory({ [HUB_VIEW_KEY]: 'lista' }))).toBe('lista')
        expect(storedHubView(memory({ [HUB_VIEW_KEY]: 'kanban' }))).toBe('lista')
        expect(storedHubView(memory())).toBe('lista')
        expect(storedHubView(null)).toBe('lista')
        expect(
            storedHubView({
                getItem: () => {
                    throw new Error('bloqueado')
                },
            }),
        ).toBe('lista')
    })

    it('guarda a escolha e não quebra sem storage', () => {
        const storage = memory()
        storeHubView('quadro', storage)
        expect(storage.data[HUB_VIEW_KEY]).toBe('quadro')
        expect(() =>
            storeHubView('lista', {
                setItem: () => {
                    throw new Error('cheio')
                },
            }),
        ).not.toThrow()
    })

    it('cada área tem a sua cor; área desconhecida usa a neutra', () => {
        expect(areaColor('Pré-protocolo')).toBe('var(--pie-4)')
        expect(areaColor('Outros')).toBe('var(--pie-rest)')
    })
})
