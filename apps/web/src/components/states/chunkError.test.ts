import { describe, expect, it } from 'vitest'
import { isChunkLoadError } from './chunkError.ts'

describe('isChunkLoadError', () => {
    it('reconhece a falha do import() de um chunk que sumiu (Chrome, Safari e Firefox)', () => {
        expect(isChunkLoadError(new TypeError('Failed to fetch dynamically imported module: /assets/x.js'))).toBe(true)
        expect(isChunkLoadError(new TypeError('Importing a module script failed.'))).toBe(true)
        expect(isChunkLoadError(new TypeError('error loading dynamically imported module'))).toBe(true)
    })

    it('não confunde com erro comum de render nem com valores que não são Error', () => {
        expect(isChunkLoadError(new Error("Cannot read properties of undefined (reading 'map')"))).toBe(false)
        expect(isChunkLoadError('dynamically imported module')).toBe(false)
        expect(isChunkLoadError(null)).toBe(false)
    })
})
