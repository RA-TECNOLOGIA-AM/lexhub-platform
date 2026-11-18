import { describe, expect, it } from 'vitest'
import { audit } from '../../../services/mock/audit.ts'
import {
    actorsOf,
    auditCsv,
    auditFilename,
    filterEvents,
    filterFromParams,
    paramsFromFilter,
    whenLabel,
} from './auditView.ts'

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

describe('exportar CSV', () => {
    const one = {
        id: '1',
        at: '2026-11-18T19:29:40Z',
        actor: 'Ana; Ribeiro',
        email: 'ana.ribeiro@lexgroup.com.br',
        kind: 'login' as const,
        action: 'Entrou',
        detail: 'Chrome · Windows · 189.10.20.30',
    }
    it('cabeçalho, data completa em Manaus, tipo por extenso e ; escapado', () => {
        const lines = auditCsv([one]).replace('﻿', '').split('\r\n')
        expect(lines[0]).toBe('Quando;Quem;Tipo;O que aconteceu;E-mail;Detalhe')
        expect(lines[1]).toBe(
            '18/11/2026 15:29:40;"Ana; Ribeiro";Entradas;Entrou;ana.ribeiro@lexgroup.com.br;Chrome · Windows · 189.10.20.30',
        )
    })
    it('nome do arquivo com a org e o dia em Manaus', () => {
        expect(auditFilename('lexgroup', new Date('2026-11-19T02:00:00Z'))).toBe('auditoria-lexgroup-2026-11-18.csv')
    })
})
