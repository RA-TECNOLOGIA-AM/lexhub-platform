import { describe, expect, it } from 'vitest'
import { DOC_ENTRIES } from './docRegistry.ts'
import { DOC_PAGES } from './docPages.ts'

describe('DOC_PAGES', () => {
    it('todo guia do registro tem conteúdo, e todo conteúdo está no registro', () => {
        expect(Object.keys(DOC_PAGES).sort()).toEqual(DOC_ENTRIES.map((d) => d.slug).sort())
    })
})
