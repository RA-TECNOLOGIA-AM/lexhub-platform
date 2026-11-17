import { describe, expect, it } from 'vitest'
import { fullscreenSupported, isFullscreen, toggleFullscreen, type FullscreenDoc } from './fullscreen.ts'

function fakeDoc(options: { enabled?: boolean; refuse?: boolean } = {}) {
    const doc: FullscreenDoc & { calls: string[] } = {
        calls: [],
        fullscreenEnabled: options.enabled ?? true,
        fullscreenElement: null,
        exitFullscreen: async () => {
            doc.calls.push('exit')
            doc.fullscreenElement = null
        },
        documentElement: {
            requestFullscreen: async () => {
                doc.calls.push('request')
                if (options.refuse) throw new TypeError('Permissions check failed')
                doc.fullscreenElement = {} as Element
            },
        },
    }
    return doc
}

describe('fullscreenSupported', () => {
    it('precisa da API e da permissão', () => {
        expect(fullscreenSupported(fakeDoc())).toBe(true)
        expect(fullscreenSupported(fakeDoc({ enabled: false }))).toBe(false)
        expect(fullscreenSupported({ documentElement: {} })).toBe(false)
    })
})

describe('toggleFullscreen', () => {
    it('entra e depois sai', async () => {
        const doc = fakeDoc()
        expect(await toggleFullscreen(doc)).toBe('entered')
        expect(isFullscreen(doc)).toBe(true)
        expect(await toggleFullscreen(doc)).toBe('exited')
        expect(isFullscreen(doc)).toBe(false)
        expect(doc.calls).toEqual(['request', 'exit'])
    })

    it('recusa do navegador vira "denied", sem erro', async () => {
        const doc = fakeDoc({ refuse: true })
        expect(await toggleFullscreen(doc)).toBe('denied')
        expect(isFullscreen(doc)).toBe(false)
    })

    it('sem suporte não chama nada', async () => {
        const doc = fakeDoc({ enabled: false })
        expect(await toggleFullscreen(doc)).toBe('unsupported')
        expect(doc.calls).toEqual([])
    })
})
