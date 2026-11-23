import { describe, expect, it } from 'vitest'
import { audit } from '../../../services/mock/audit.ts'
import { members } from '../../../services/mock/members.ts'
import {
    actorsOf,
    auditCsv,
    auditFilename,
    filterEvents,
    filterFromParams,
    filterNever,
    NEVER,
    neverAccessed,
    neverCsv,
    paramsFromFilter,
    customRange,
    queryFromFilter,
    whenLabel,
} from './auditView.ts'

const events = audit.events
const all = { kind: '' as const, actor: '', unit: '', org: '', period: '7' as const, de: '', ate: '' }

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
        expect(filterEvents(events, { ...all, kind: 'export', actor: 'Ana Ribeiro' })).toEqual([])
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
        const f = { ...all, kind: 'export' as const, actor: 'Bruno Melo' }
        expect(filterFromParams(paramsFromFilter(f))).toEqual(f)
        expect(paramsFromFilter(f).toString()).toBe('tipo=export&pessoa=Bruno+Melo')
    })
    it('período: 7 dias é o padrão e não vai para a URL; 30/90 e datas vão e voltam', () => {
        expect(filterFromParams(new URLSearchParams('')).period).toBe('7')
        const trinta = { ...all, period: '30' as const }
        expect(paramsFromFilter(trinta).toString()).toBe('periodo=30')
        expect(filterFromParams(paramsFromFilter(trinta))).toEqual(trinta)
        const datas = { ...all, period: 'custom' as const, de: '2026-11-01', ate: '2026-11-10' }
        expect(paramsFromFilter(datas).toString()).toBe('periodo=custom&de=2026-11-01&ate=2026-11-10')
        expect(filterFromParams(paramsFromFilter(datas))).toEqual(datas)
    })
    it('período inválido na URL volta para 7 dias', () => {
        expect(filterFromParams(new URLSearchParams('periodo=365')).period).toBe('7')
        expect(filterFromParams(new URLSearchParams('periodo=custom&de=lixo&ate=2026-11-10'))).toMatchObject({
            period: '7',
            de: '',
            ate: '',
        })
        expect(filterFromParams(new URLSearchParams('periodo=custom&de=2026-11-10&ate=2026-11-01')).period).toBe('7')
    })
    it('tipo inválido na URL vira "todos"', () => {
        expect(filterFromParams(new URLSearchParams('tipo=ataque')).kind).toBe('')
    })
})

describe('consulta ao banco', () => {
    const now = new Date('2026-11-19T12:00:00-04:00')
    it('últimos N dias: desde agora menos N dias, sem fim', () => {
        expect(queryFromFilter({ ...all, kind: 'view', actor: 'Ana Ribeiro' }, now)).toEqual({
            from: '2026-11-12T16:00:00.000Z',
            to: null,
            kind: 'view',
            actor: 'Ana Ribeiro',
            unit: '',
        })
        expect(queryFromFilter({ ...all, period: '90' }, now).from).toBe('2026-08-21T16:00:00.000Z')
    })
    it('datas livres: do começo do "de" ao fim do "até", no fuso de Manaus', () => {
        const q = queryFromFilter({ ...all, period: 'custom', de: '2026-11-01', ate: '2026-11-30' }, now)
        expect(q).toEqual({
            from: '2026-11-01T00:00:00-04:00',
            to: '2026-12-01T00:00:00-04:00',
            kind: '',
            actor: '',
            unit: '',
        })
    })
    it('ao escolher datas, começa nos últimos 7 dias (dia de Manaus)', () => {
        expect(customRange(new Date('2026-11-20T02:00:00Z'))).toEqual({ de: '2026-11-12', ate: '2026-11-19' })
    })
    it('"Nunca acessou" não filtra eventos por tipo', () => {
        expect(queryFromFilter({ ...all, kind: NEVER }, now).kind).toBe('')
    })
})

describe('organização e unidade na URL', () => {
    it('ida e volta, com o código em maiúsculas e o slug em minúsculas', () => {
        const f = filterFromParams(new URLSearchParams('unidade=ng&org=Org-Teste'))
        expect(f).toMatchObject({ unit: 'NG', org: 'org-teste' })
        expect(paramsFromFilter(f).toString()).toBe('unidade=NG&org=org-teste')
    })
    it('a unidade vai para o banco', () => {
        expect(queryFromFilter({ ...all, unit: 'LA' }).unit).toBe('LA')
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

describe('nunca acessou', () => {
    it('lê "nunca" da URL e devolve na URL', () => {
        const f = filterFromParams(new URLSearchParams('tipo=nunca'))
        expect(f.kind).toBe(NEVER)
        expect(paramsFromFilter(f).toString()).toBe('tipo=nunca')
    })
    it('lista membros sem last_seen_at e convites; ignora desativados', () => {
        const rows = neverAccessed(members)
        const ids = rows.map((r) => r.id)
        for (const m of members.members) {
            const expected = !m.last_seen_at && m.status !== 'disabled'
            expect(ids.includes(m.id)).toBe(expected)
        }
        expect(rows.filter((r) => r.status === 'Convite pendente')).toHaveLength(members.invitations.length)
    })
    it('filtra por pessoa e gera CSV', () => {
        const rows = neverAccessed(members)
        expect(filterNever(rows, rows[0].name)).toEqual([rows[0]])
        expect(neverCsv(rows).split('\n')[0]).toContain('Situação')
    })
})
