import type { AuditEvent, AuditKind, RawAuditEvent } from '../types/index.ts'
import { ROLE_LABEL } from '../pages/admin/members/memberView.ts'
import { KIND } from '../pages/admin/audit/auditView.ts'
import { describeUserAgent } from './userAgent.ts'

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
// 'lexpre' -> 'LexPre'
const product = (v: unknown): string | null => ({ lexpre: 'LexPre', lexflow: 'LexFlow' })[text(v) ?? ''] ?? text(v)
// 'postgres' -> 'Postgres', 'sheets' -> 'Google Planilhas'
const connectorLabel = (v: unknown): string | null =>
    ({ postgres: 'Postgres', mysql: 'MySQL', sheets: 'Google Planilhas' })[text(v) ?? ''] ?? text(v)
// Junta as partes que existem: 'a · b · c'
const join = (...parts: (string | null | undefined)[]): string => parts.filter(Boolean).join(' · ')

type Rule = { kind: AuditKind; action: string; detail: (e: RawAuditEvent, m: Meta) => string }

const EVENTS: Record<string, Rule> = {
    'auth.login': {
        kind: 'login',
        action: 'Entrou',
        detail: (_, m) => join(describeUserAgent(text(m.userAgent)), text(m.ip)),
    },
    'audit.export': {
        kind: 'export',
        action: 'Exportou a auditoria',
        detail: (_, m) => {
            const rows = num(m.rows)
            const kind = text(m.kind)
            return join(
                rows === null ? null : `${nf.format(rows)} eventos`,
                kind && (KIND[kind as AuditKind]?.label ?? kind),
                text(m.actor),
                text(m.format)?.toUpperCase(),
            )
        },
    },
    'dashboard.view': {
        kind: 'view',
        action: 'Abriu dashboard',
        detail: (e, m) => join(e.targetName ?? e.targetId, text(m.unit)),
    },
    // Modo suporte: o ator é quem pediu (Owner/Dev); o alvo (targetName) é o membro visto.
    'support.started': {
        kind: 'support',
        action: 'Iniciou suporte',
        detail: (e, m) =>
            `como ${e.targetName ?? e.targetId ?? 'membro'}${text(m.reason) ? `: ${text(m.reason)}` : ''}`,
    },
    'support.viewed': {
        kind: 'support',
        action: 'Abriu dashboard em suporte',
        detail: (e, m) =>
            join(
                text(m.dashboard) && `${text(m.dashboard)}${text(m.unit) ? ` (${text(m.unit)})` : ''}`,
                `como ${e.targetName ?? e.targetId ?? 'membro'}`,
            ),
    },
    'support.ended': {
        kind: 'support',
        action: 'Encerrou suporte',
        detail: (e, m) =>
            join(e.targetName ?? e.targetId, { exit: 'saiu', expired: 'venceu' }[text(m.end_reason) ?? ''] ?? null),
    },
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
    'unit.deleted': {
        kind: 'source',
        action: 'Excluiu unidade',
        detail: (e, m) => join(text(m.name) ?? e.targetName, text(m.code)),
    },
    'unit.restored': {
        kind: 'source',
        action: 'Restaurou unidade',
        detail: (e, m) => join(text(m.name) ?? e.targetName, text(m.code)),
    },
    'org.reopened': {
        kind: 'access',
        action: 'Reabriu organização',
        detail: (_, m) => join(text(m.name), text(m.slug)),
    },
    'org.purged': {
        kind: 'access',
        action: 'Apagou organização de vez',
        detail: (_, m) => join(text(m.name), text(m.slug)),
    },
    'org.closed': {
        kind: 'access',
        action: 'Encerrou organização',
        detail: (_, m) => join(text(m.name), text(m.slug)),
    },
    'source.office_linked': {
        kind: 'source',
        action: 'Ligou escritório',
        detail: (_, m) => join(text(m.unit), product(m.product), text(m.office) && `escritório ${text(m.office)}`),
    },
    'source.connected': {
        kind: 'source',
        action: 'Conectou fonte',
        detail: (_, m) =>
            join(
                text(m.name),
                text(m.unit),
                connectorLabel(m.connector),
                text(m.host),
                text(m.tab) && `aba ${text(m.tab)}`,
                m.writerAck === true ? 'usuário que pode escrever' : null,
            ),
    },
    'source.secret_changed': {
        kind: 'source',
        action: 'Trocou a senha da fonte',
        detail: (_, m) => join(text(m.name), connectorLabel(m.connector)),
    },
    'source.disconnected': {
        kind: 'source',
        action: 'Desconectou fonte',
        detail: (_, m) => join(text(m.name), connectorLabel(m.connector)),
    },
    'source.disabled': {
        kind: 'source',
        action: 'Desligou fonte',
        detail: (_, m) => join(text(m.name), connectorLabel(m.connector), 'ligada → desligada'),
    },
    'source.enabled': {
        kind: 'source',
        action: 'Religou fonte',
        detail: (_, m) => join(text(m.name), connectorLabel(m.connector), 'desligada → ligada'),
    },
    'source.office_unlinked': {
        kind: 'source',
        action: 'Desligou escritório',
        detail: (_, m) => join(text(m.unit), product(m.product)),
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

// Opções do filtro "Tipo de evento": só os tipos que algum evento usa, em ordem alfabética, com "Outros" no fim.
export const kindOptions = (): AuditKind[] => [
    ...[...new Set(Object.values(EVENTS).map((r) => r.kind))].sort((a, b) =>
        KIND[a].label.localeCompare(KIND[b].label, 'pt-BR'),
    ),
    'other',
]

// O filtro de tipo que o banco aplica (api.list_audit). Um tipo = só os eventos dele. "Outros" = tudo menos os
// eventos que têm regra aqui (os desconhecidos). '' (todos) = sem filtro.
export function actionFilter(kind: AuditKind | ''): {
    p_actions: string[] | null
    p_exclude_actions: string[] | null
} {
    const known = Object.keys(EVENTS)
    if (!kind) return { p_actions: null, p_exclude_actions: null }
    if (kind === 'other') return { p_actions: null, p_exclude_actions: known }
    return { p_actions: known.filter((action) => EVENTS[action]?.kind === kind), p_exclude_actions: null }
}

export function toAuditEvent(e: RawAuditEvent): AuditEvent {
    const rule = EVENTS[e.action]
    const m = e.metadata ?? {}
    return {
        id: e.id,
        at: e.at,
        actor: e.actor,
        email: e.actorEmail ?? null,
        kind: rule?.kind ?? 'other',
        action: rule?.action ?? e.action,
        detail: rule ? rule.detail(e, m) : (e.targetName ?? e.targetId ?? ''),
    }
}
