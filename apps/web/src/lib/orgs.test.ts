import { describe, expect, it } from 'vitest'
import { meFor } from '../services/mock/users.ts'
import { orgDecision, orgInitials } from './orgs.ts'

describe('orgInitials', () => {
    it('duas palavras: a primeira letra de cada', () => {
        expect(orgInitials('Cliente parceiro')).toBe('CP')
    })
    it('uma palavra: as maiúsculas dela, ou as duas primeiras letras', () => {
        expect(orgInitials('LexGroup')).toBe('LG')
        expect(orgInitials('Advocacia')).toBe('AD')
    })
    it('ignora símbolos e aceita acento', () => {
        expect(orgInitials('[ESCRITÓRIO]')).toBe('ES')
        expect(orgInitials('Órion Jurídico')).toBe('ÓJ')
    })
})

describe('orgDecision', () => {
    const lexgroup = meFor('lexgroup')!
    it('a organização ativa aparece direto', () => {
        expect(orgDecision('lexgroup', lexgroup)).toBe('show')
    })
    it('outra organização da pessoa: trocar', () => {
        expect(orgDecision('cliente-parceiro', lexgroup)).toBe('switch')
    })
    it('organização de que a pessoa não faz parte: negar', () => {
        expect(orgDecision('outra-empresa', lexgroup)).toBe('deny')
    })
})
