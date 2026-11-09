import { describe, expect, it } from 'vitest'
import { members } from '../../data/mock/members.ts'
import { filterFromParams, filterMembers, paramsFromFilter } from './memberView.ts'

const all = members.members
const names = (list: typeof all) => list.map((m) => m.email.split('@')[0])
const none = { q: '', unit: '', role: '' as const }

describe('filterMembers', () => {
    it('sem filtro mostra todos', () => {
        expect(filterMembers(all, none)).toHaveLength(6)
    })
    it('busca por nome ou e-mail, sem diferenciar maiúscula e acento', () => {
        expect(names(filterMembers(all, { ...none, q: 'ANA' }))).toEqual(['ana'])
        expect(names(filterMembers(all, { ...none, q: 'diego@' }))).toEqual(['diego'])
        expect(names(filterMembers(all, { ...none, q: 'fernánda' }))).toEqual(['fernanda'])
    })
    it('unidade inclui quem está em todas as unidades', () => {
        expect(names(filterMembers(all, { ...none, unit: 'LA_RJ' }))).toEqual(['ana', 'carla'])
    })
    it('papel e unidade juntos', () => {
        expect(names(filterMembers(all, { ...none, unit: 'NG', role: 'colaborador' }))).toEqual(['diego'])
    })
})

describe('filtro na URL', () => {
    it('vai e volta', () => {
        const f = { q: 'ana', unit: 'NG', role: 'gestor' as const }
        expect(filterFromParams(paramsFromFilter(f))).toEqual(f)
        expect(paramsFromFilter(f).toString()).toBe('busca=ana&unidade=NG&papel=gestor')
    })
    it('campos vazios não vão para a URL', () => {
        expect(paramsFromFilter(none).toString()).toBe('')
    })
    it('papel inválido na URL vira "todos"', () => {
        expect(filterFromParams(new URLSearchParams('papel=chefe')).role).toBe('')
    })
})
