import { describe, expect, it } from 'vitest'
import { audit } from '../../../services/mock/audit.ts'
import { actorsOf, filterEvents, filterFromParams, paramsFromFilter, whenLabel } from './auditView.ts'

const events = audit.events
const all = { kind: '' as const, actor: '' }

describe('whenLabel', () => {
    it('mostra dia/mês e hora no fuso de Manaus', () => {
        expect(whenLabel('2026-10-30T14:02:00-04:00')).toBe('30/10 14:02')
    })
    it('converte de outro fuso (meia-noite UTC = 20h da véspera em Manaus)', () => {
        expect(whenLabel('2026-10-30T00:00:00Z')).toBe('29/10 20:00')
    })
    it('aceita outro fuso', () => {
        expect(whenLabel('2026-10-30T14:02:00-04:00', 'America/Sao_Paulo')).toBe('30/10 15:02')
    })
})

describe('filtros', () => {
    it('sem filtro mostra todos', () => {
        expect(filterEvents(events, all)).toHaveLength(6)
    })
    it('por tipo e por pessoa', () => {
        expect(filterEvents(events, { ...all, kind: 'access' }).map((e) => e.id)).toEqual(['ev6', 'ev3'])
        expect(filterEvents(events, { kind: 'export', actor: 'Ana Ribeiro' })).toEqual([])
        expect(filterEvents(events, { ...all, actor: 'Bruno Melo' }).map((e) => e.action)).toEqual(['Exportou dados'])
    })
    it('pessoas sem repetir, em ordem alfabética', () => {
        expect(actorsOf(events)).toEqual([
            'Ana Ribeiro',
            'Bruno Melo',
            'Carla Souza',
            'Sistema',
            'Suporte RA Tecnologia',
        ])
    })
})

describe('filtro na URL', () => {
    it('vai e volta', () => {
        const f = { kind: 'export' as const, actor: 'Bruno Melo' }
        expect(filterFromParams(paramsFromFilter(f))).toEqual(f)
        expect(paramsFromFilter(f).toString()).toBe('tipo=export&pessoa=Bruno+Melo')
    })
    it('tipo inválido na URL vira "todos"', () => {
        expect(filterFromParams(new URLSearchParams('tipo=ataque')).kind).toBe('')
    })
})
