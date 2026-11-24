import { describe, expect, it } from 'vitest'
import { detectSystem, shortcutRows } from './atalhos.ts'

describe('detectSystem', () => {
    it('Mac, iPhone e iPad = mac; Windows, Linux e Android = windows', () => {
        expect(detectSystem('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15')).toBe('mac')
        expect(detectSystem('Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X)')).toBe('mac')
        expect(detectSystem('Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0')).toBe('windows')
        expect(detectSystem('Mozilla/5.0 (X11; Linux x86_64)')).toBe('windows')
        expect(detectSystem('')).toBe('windows')
    })
})

describe('shortcutRows', () => {
    it('troca as teclas pelo sistema e mantém o que cada atalho faz', () => {
        const win = shortcutRows('windows')
        const mac = shortcutRows('mac')
        expect(win.map((r) => r[1])).toEqual(mac.map((r) => r[1]))
        expect(win.map((r) => r[0])).toContain('Ctrl + clique')
        expect(mac.map((r) => r[0])).toContain('⌘ Command + clique')
        expect(mac.map((r) => r[0])).not.toContain('F11')
    })
})
