import { describe, expect, it } from 'vitest'
import type { RawAuditEvent } from '../types/index.ts'
import { actionFilter, kindOptions, toAuditEvent } from './auditEvents.ts'

const raw = (over: Partial<RawAuditEvent>): RawAuditEvent => ({
    id: '1',
    at: '2026-11-13T10:00:00-04:00',
    action: 'x',
    actor: 'Ana Ribeiro',
    targetType: null,
    targetId: null,
    targetName: null,
    metadata: {},
    ...over,
})

describe('toAuditEvent', () => {
    it('senha da conta: criou ou alterou, pelo metadata.kind', () => {
        expect(toAuditEvent(raw({ action: 'auth.password_changed', metadata: { kind: 'created' } }))).toMatchObject({
            kind: 'account',
            action: 'Criou a senha',
            detail: '',
        })
        expect(toAuditEvent(raw({ action: 'auth.password_changed', metadata: { kind: 'changed' } }))).toMatchObject({
            kind: 'account',
            action: 'Alterou a senha',
        })
        expect(actionFilter('account').p_actions).toEqual(['auth.session_revoked', 'auth.password_changed'])
        expect(actionFilter('login').p_actions).not.toContain('auth.password_changed')
    })

    it('entrada: navegador, sistema e IP', () => {
        const e = toAuditEvent(
            raw({
                action: 'auth.login',
                metadata: {
                    ip: '189.10.20.30',
                    userAgent:
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36',
                },
            }),
        )
        expect(e).toMatchObject({ kind: 'login', action: 'Entrou' })
        expect(toAuditEvent(raw({ actorEmail: 'ana@lexgroup.com.br' })).email).toBe('ana@lexgroup.com.br')
        expect(toAuditEvent(raw({})).email).toBeNull()
        expect(e.detail).toBe('Chrome · Windows · 189.10.20.30')
    })

    it('entrada sem navegador conhecido: só o IP; pela TV: TV (QR)', () => {
        expect(toAuditEvent(raw({ action: 'auth.login', metadata: { ip: '10.0.0.1' } })).detail).toBe('10.0.0.1')
        expect(toAuditEvent(raw({ action: 'auth.login', metadata: { userAgent: 'python-httpx/0.27.0' } })).detail).toBe(
            'TV (QR)',
        )
    })

    it('dashboard aberto: nome do dashboard e unidade', () => {
        const e = toAuditEvent(
            raw({
                action: 'dashboard.view',
                targetType: 'dashboard',
                targetId: 'comercial-lexpre',
                targetName: 'Comercial (LexPre)',
                metadata: { org: 'lexgroup', unit: 'NG' },
            }),
        )
        expect(e).toMatchObject({ kind: 'view', action: 'Abriu dashboard', detail: 'Comercial (LexPre) · NG' })
    })

    it('exportação: dashboard, unidade, período, linhas e formato', () => {
        const e = toAuditEvent(
            raw({
                action: 'dashboard.export',
                targetId: 'pendencias',
                targetName: 'Pendências',
                metadata: { unit: 'NG', from: '2026-11-01', to: '2026-11-11', rows: 1184, format: 'xlsx' },
            }),
        )
        expect(e).toMatchObject({ kind: 'export', action: 'Exportou dados', actor: 'Ana Ribeiro' })
        expect(e.detail).toBe('Pendências · NG · 01/11 a 11/11 · 1.184 linhas · XLSX')
    })

    it('convite: e-mail, papel e unidades', () => {
        const e = toAuditEvent(
            raw({
                action: 'member.invited',
                targetId: 'bia@lexgroup.com.br',
                metadata: { role: 'colaborador', units: ['NG', 'RJ'] },
            }),
        )
        expect(e).toMatchObject({ kind: 'access', action: 'Convidou pessoa' })
        expect(e.detail).toBe('bia@lexgroup.com.br · Colaborador · NG, RJ')
    })

    it('unidade editada: mostra só o que mudou', () => {
        const e = toAuditEvent(
            raw({
                action: 'unit.updated',
                targetName: 'LAAM',
                metadata: {
                    code: 'LA',
                    before: { name: 'LAAM', timezone: 'America/Manaus' },
                    after: { name: 'LAAM', timezone: 'America/Sao_Paulo' },
                },
            }),
        )
        expect(e).toMatchObject({ kind: 'source', action: 'Editou unidade' })
        expect(e.detail).toBe('LAAM · America/Manaus → America/Sao_Paulo')
    })

    it('importação sem pessoa e evento desconhecido', () => {
        expect(
            toAuditEvent(raw({ action: 'import.v1', actor: 'Sistema', metadata: { members: 87, units: 5 } })),
        ).toMatchObject({
            actor: 'Sistema',
            detail: '87 pessoas · 5 unidades',
        })
        expect(toAuditEvent(raw({ action: 'algo.novo', targetName: 'Alvo' }))).toMatchObject({
            kind: 'other',
            action: 'algo.novo',
            detail: 'Alvo',
        })
    })

    it('metadata estranha não quebra a linha', () => {
        const e = toAuditEvent(raw({ action: 'dashboard.export', metadata: { rows: 'muitas', from: 3 } }))
        expect(e.detail).toBe('')
    })
})

describe('exportação da auditoria', () => {
    it('quantos eventos, filtro e formato', () => {
        const e = toAuditEvent(
            raw({
                action: 'audit.export',
                metadata: { rows: 1204, kind: 'login', actor: 'Nicolas Gomes', format: 'csv' },
            }),
        )
        expect(e).toMatchObject({ kind: 'export', action: 'Exportou a auditoria' })
        expect(e.detail).toBe('1.204 eventos · Entradas · Nicolas Gomes · CSV')
    })
})

describe('actionFilter', () => {
    it('desconectou um aparelho: tipo Segurança da conta, com navegador e IP', () => {
        const e = toAuditEvent(
            raw({ action: 'auth.session_revoked', metadata: { ip: '10.0.0.2', userAgent: 'python-httpx/0.27.0' } }),
        )
        expect(e.kind).toBe('account')
        expect(e.action).toBe('Desconectou um aparelho')
        expect(e.detail).toBe('TV (QR) · 10.0.0.2')
    })

    it('um tipo: o banco traz só os eventos dele', () => {
        expect(actionFilter('view')).toEqual({ p_actions: ['dashboard.view'], p_exclude_actions: null })
        expect(actionFilter('export').p_actions).toEqual(expect.arrayContaining(['dashboard.export', 'audit.export']))
    })

    it('"Outros": o banco traz tudo menos os tipos conhecidos', () => {
        const f = actionFilter('other')
        expect(f.p_actions).toBeNull()
        expect(f.p_exclude_actions).toEqual(
            expect.arrayContaining(['dashboard.view', 'auth.login', 'dashboard.export']),
        )
    })

    it('"Todos": sem filtro de tipo', () => {
        expect(actionFilter('')).toEqual({ p_actions: null, p_exclude_actions: null })
    })
})

describe('kindOptions', () => {
    it('tipos com evento e Outros, todos em ordem alfabética', () => {
        expect(kindOptions()).toEqual(['view', 'login', 'export', 'access', 'other', 'account', 'support', 'source'])
    })
})

describe('modo suporte', () => {
    const member = { targetType: 'membership', targetId: 'm1', targetName: 'Bruna Lima' }

    it('iniciou: com quem e o motivo', () => {
        const e = toAuditEvent(
            raw({ action: 'support.started', ...member, metadata: { session: 's1', reason: '#4521' } }),
        )
        expect(e).toMatchObject({ kind: 'support', action: 'Iniciou suporte', detail: 'como Bruna Lima: #4521' })
    })

    it('abriu dashboard: dashboard, unidade e como quem', () => {
        const e = toAuditEvent(
            raw({
                action: 'support.viewed',
                ...member,
                metadata: { session: 's1', unit: 'NG', dashboard: 'comercial' },
            }),
        )
        expect(e).toMatchObject({ kind: 'support', action: 'Abriu dashboard em suporte' })
        expect(e.detail).toBe('comercial (NG) · como Bruna Lima')
    })

    it('encerrou: saiu ou venceu', () => {
        const ended = (end_reason: string) =>
            toAuditEvent(raw({ action: 'support.ended', ...member, metadata: { session: 's1', end_reason } }))
        expect(ended('exit')).toMatchObject({
            kind: 'support',
            action: 'Encerrou suporte',
            detail: 'Bruna Lima · saiu',
        })
        expect(ended('expired').detail).toBe('Bruna Lima · venceu')
    })

    it('filtro Suporte traz os três eventos', () => {
        expect(actionFilter('support').p_actions).toEqual(['support.started', 'support.viewed', 'support.ended'])
    })
})
