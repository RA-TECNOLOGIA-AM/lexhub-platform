import type { AuditEvent, AuditKind, RawAuditEvent } from '../types/index.ts'
import { ROLE_LABEL } from '../pages/admin/members/memberView.ts'

// Módulo: traduz o evento cru do banco (app.audit_log, via api.list_audit) para a linha da tela de Auditoria.
// Evento novo = uma entrada em EVENTS. Evento desconhecido aparece como 'Outros', com o nome cru.

type Meta = Record<string, unknown>

const text = (v: unknown): string | null => (typeof v === 'string' && v.trim() ? v : null)
const num = (v: unknown): number | null => (typeof v === 'number' ? v : null)
const list = (v: unknown): string[] => (Array.isArray(v) ? v.filter((x): x is string => typeof x === 'string') : [])
const role = (v: unknown): string | null => {
    const key = text(v)
    return key ? (ROLE_LABEL[key as keyof typeof ROLE_LABEL] ?? key) : null
}
const nf = new Intl.NumberFormat('pt-BR')
// '2026-11-01' -> '01/11'
const day = (v: unknown): string | null => {
    const s = text(v)
    return s && /^\d{4}-\d{2}-\d{2}/.test(s) ? `${s.slice(8, 10)}/${s.slice(5, 7)}` : null
}
// Junta as partes que existem: 'a · b · c'
const join = (...parts: (string | null | undefined)[]): string => parts.filter(Boolean).join(' · ')

type Rule = { kind: AuditKind; action: string; detail: (e: RawAuditEvent, m: Meta) => string }

const EVENTS: Record<string, Rule> = {
    'dashboard.export': {
        kind: 'export',
        action: 'Exportou dados',
        detail: (e, m) => {
            const from = day(m.from)
            const to = day(m.to)
            const rows = num(m.rows)
            return join(
                e.targetName ?? e.targetId,
                text(m.unit),
                from && to ? `${from} a ${to}` : null,
                rows === null ? null : `${nf.format(rows)} linhas`,
                text(m.format)?.toUpperCase(),
            )
        },
    },
    'member.invited': {
        kind: 'access',
        action: 'Convidou pessoa',
        detail: (e, m) => join(e.targetId, role(m.role), list(m.units).join(', ') || null),
    },
    'invitation.revoked': { kind: 'access', action: 'Cancelou convite', detail: (_, m) => text(m.email) ?? '' },
    'invitation.accepted': { kind: 'login', action: 'Aceitou convite', detail: (_, m) => role(m.role) ?? '' },
    'member.disabled': {
        kind: 'access',
        action: 'Desativou membro',
        detail: (e, m) => text(m.email) ?? e.targetName ?? '',
    },
    'member.enabled': {
        kind: 'access',
        action: 'Reativou membro',
        detail: (e, m) => text(m.email) ?? e.targetName ?? '',
    },
    'member.access_updated': { kind: 'access', action: 'Mudou acesso', detail: (e) => e.targetName ?? '' },
    'access_request.approved': {
        kind: 'access',
        action: 'Aprovou pedido de acesso',
        detail: (_, m) => role(m.org_role) ?? '',
    },
    'unit.created': {
        kind: 'source',
        action: 'Criou unidade',
        detail: (_, m) => join(text(m.name), text(m.code), text(m.timezone)),
    },
    'unit.updated': {
        kind: 'source',
        action: 'Editou unidade',
        detail: (e, m) => {
            const before = (m.before ?? {}) as Meta
            const after = (m.after ?? {}) as Meta
            const changes = (['name', 'timezone'] as const)
                .filter((k) => before[k] !== after[k])
                .map((k) => `${text(before[k]) ?? '—'} → ${text(after[k]) ?? '—'}`)
            return join(e.targetName ?? text(m.code), ...changes)
        },
    },
    'import.v1': {
        kind: 'source',
        action: 'Importou da v1',
        detail: (_, m) =>
            join(
                num(m.members) === null ? null : `${m.members} pessoas`,
                num(m.units) === null ? null : `${m.units} unidades`,
            ),
    },
}

export function toAuditEvent(e: RawAuditEvent): AuditEvent {
    const rule = EVENTS[e.action]
    const m = e.metadata ?? {}
    return {
        id: e.id,
        at: e.at,
        actor: e.actor,
        kind: rule?.kind ?? 'other',
        action: rule?.action ?? e.action,
        detail: rule ? rule.detail(e, m) : (e.targetName ?? e.targetId ?? ''),
    }
}
