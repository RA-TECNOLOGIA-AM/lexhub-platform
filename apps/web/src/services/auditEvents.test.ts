import { describe, expect, it } from 'vitest'
import type { RawAuditEvent } from '../types/index.ts'
import { toAuditEvent } from './auditEvents.ts'

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
