import { describe, expect, it } from 'vitest'
import { avatarFileError, squareCrop } from './avatarImage.ts'

describe('avatarFileError', () => {
    it('aceita JPG, PNG e WebP até 10 MB', () => {
        expect(avatarFileError({ type: 'image/jpeg', size: 1_000 })).toBeNull()
        expect(avatarFileError({ type: 'image/png', size: 10 * 1024 * 1024 })).toBeNull()
        expect(avatarFileError({ type: 'image/webp', size: 1 })).toBeNull()
    })

    it('recusa outros formatos e arquivos grandes', () => {
        expect(avatarFileError({ type: 'image/gif', size: 1 })).toMatch(/JPG, PNG ou WebP/)
        expect(avatarFileError({ type: 'application/pdf', size: 1 })).toMatch(/JPG, PNG ou WebP/)
        expect(avatarFileError({ type: 'image/jpeg', size: 10 * 1024 * 1024 + 1 })).toMatch(/10 MB/)
    })
})

describe('squareCrop', () => {
    it('pega o quadrado do meio', () => {
        expect(squareCrop(400, 200)).toEqual({ x: 100, y: 0, size: 200 })
        expect(squareCrop(200, 400)).toEqual({ x: 0, y: 100, size: 200 })
        expect(squareCrop(300, 300)).toEqual({ x: 0, y: 0, size: 300 })
    })
})
