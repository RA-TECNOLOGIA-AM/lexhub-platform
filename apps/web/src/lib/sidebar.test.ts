import { describe, expect, it } from 'vitest'
import { SIDEBAR_KEY, storedSidebarCollapsed, storeSidebarCollapsed } from './sidebar.ts'

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

describe('storedSidebarCollapsed', () => {
    it('lê a escolha guardada', () => {
        expect(storedSidebarCollapsed(memory({ [SIDEBAR_KEY]: 'collapsed' }))).toBe(true)
        expect(storedSidebarCollapsed(memory({ [SIDEBAR_KEY]: 'expanded' }))).toBe(false)
    })

    it('sem escolha, valor estranho ou storage que falha: aberta', () => {
        expect(storedSidebarCollapsed(memory())).toBe(false)
        expect(storedSidebarCollapsed(memory({ [SIDEBAR_KEY]: 'sim' }))).toBe(false)
        expect(storedSidebarCollapsed(null)).toBe(false)
        const broken = {
            getItem: () => {
                throw new Error('bloqueado')
            },
        }
        expect(storedSidebarCollapsed(broken)).toBe(false)
    })
})

describe('storeSidebarCollapsed', () => {
    it('guarda a escolha e volta igual na leitura', () => {
        const storage = memory()
        storeSidebarCollapsed(true, storage)
        expect(storedSidebarCollapsed(storage)).toBe(true)
        storeSidebarCollapsed(false, storage)
        expect(storage.data[SIDEBAR_KEY]).toBe('expanded')
    })

    it('não quebra sem storage ou com storage que falha', () => {
        expect(() => storeSidebarCollapsed(true, null)).not.toThrow()
        const broken = {
            setItem: () => {
                throw new Error('cheio')
            },
        }
        expect(() => storeSidebarCollapsed(true, broken)).not.toThrow()
    })
})
