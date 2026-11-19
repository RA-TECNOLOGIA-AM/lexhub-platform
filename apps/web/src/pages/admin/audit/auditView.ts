import type { AuditEvent, AuditKind, MembersResponse } from '../../../types/index.ts'
import { toCsv, type CsvColumn } from '../../../lib/csv.ts'

// Nome no filtro "Tipo de evento" e cor do selo de cada tipo.
export const KIND: Record<AuditKind, { label: string; badge: string }> = {
    login: { label: 'Entradas', badge: 'badge neutral' },
    export: { label: 'Exportações', badge: 'badge info' },
    access: { label: 'Acesso', badge: 'badge neutral' },
    support: { label: 'Suporte', badge: 'badge pro' },
    source: { label: 'Unidades e fontes', badge: 'badge warn' },
    other: { label: 'Outros', badge: 'badge neutral' },
}

// '2026-10-30T14:02:00-04:00' -> '30/10 14:02' no fuso informado (padrão: Manaus, onde fica a LexGroup).
export function whenLabel(iso: string, timeZone = 'America/Manaus'): string {
    const parts = new Intl.DateTimeFormat('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hourCycle: 'h23',
        timeZone,
    }).formatToParts(new Date(iso))
    const get = (type: string) => parts.find((p) => p.type === type)?.value ?? ''
    return `${get('day')}/${get('month')} ${get('hour')}:${get('minute')}`
}

// --- Exportar CSV: as mesmas linhas da tela, com data completa (o arquivo pode ser lido meses depois) ---
const fullWhen = (iso: string, timeZone = 'America/Manaus'): string =>
    new Intl.DateTimeFormat('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hourCycle: 'h23',
        timeZone,
    })
        .format(new Date(iso))
        .replace(',', '')

const CSV_COLUMNS: CsvColumn[] = [
    { key: 'when', label: 'Quando' },
    { key: 'actor', label: 'Quem' },
    { key: 'kind', label: 'Tipo' },
    { key: 'action', label: 'O que aconteceu' },
    { key: 'email', label: 'E-mail' },
    { key: 'detail', label: 'Detalhe' },
]

export const auditCsv = (events: AuditEvent[]): string =>
    toCsv(
        CSV_COLUMNS,
        events.map((e) => ({
            when: fullWhen(e.at),
            actor: e.actor,
            kind: KIND[e.kind].label,
            action: e.action,
            email: e.email,
            detail: e.detail,
        })),
    )

// 'lexgroup', 2026-11-18 -> 'auditoria-lexgroup-2026-11-18.csv'
export const auditFilename = (org: string, today = new Date()): string =>
    `auditoria-${org}-${today.toLocaleDateString('sv-SE', { timeZone: 'America/Manaus' })}.csv`

// Quem aparece nos eventos, sem repetir e em ordem alfabética (opções do filtro "Pessoa").
export const actorsOf = (events: AuditEvent[]): string[] =>
    [...new Set(events.map((e) => e.actor))].sort((a, b) => a.localeCompare(b, 'pt-BR'))

// --- Filtros (Tipo de evento, Pessoa) ---
// 'nunca' = "Nunca acessou": não é um evento, é quem nunca entrou (a tela troca para a lista de pessoas).
export const NEVER = 'nunca'
export const NEVER_LABEL = 'Nunca acessou'
export type AuditFilter = { kind: AuditKind | typeof NEVER | ''; actor: string } // '' = todos / todas

export const filterEvents = (events: AuditEvent[], f: AuditFilter): AuditEvent[] =>
    events.filter((e) => (!f.kind || e.kind === f.kind) && (!f.actor || e.actor === f.actor))

// Filtro <-> URL (?tipo=&pessoa=). Tipo desconhecido na URL vira "todos".
export function filterFromParams(params: URLSearchParams): AuditFilter {
    const kind = params.get('tipo') ?? ''
    const known = kind === NEVER || kind in KIND
    return { kind: known ? (kind as AuditFilter['kind']) : '', actor: params.get('pessoa') ?? '' }
}

export function paramsFromFilter(f: AuditFilter): URLSearchParams {
    const params = new URLSearchParams()
    if (f.kind) params.set('tipo', f.kind)
    if (f.actor) params.set('pessoa', f.actor)
    return params
}

// --- Nunca acessou: membros que nunca entraram e convites ainda não aceitos ---
export type NeverRow = {
    id: string
    name: string // convite ainda não tem nome: mostra o e-mail
    email: string
    status: 'Membro' | 'Convite pendente'
    since: string | null // convite: quando foi enviado; membro: sem data
}

// Ordem alfabética. Pessoa desativada fica de fora (não pode mais entrar).
export function neverAccessed(data: MembersResponse): NeverRow[] {
    const members = data.members
        .filter((m) => !m.last_seen_at && m.status !== 'disabled')
        .map((m): NeverRow => ({ id: m.id, name: m.name, email: m.email, status: 'Membro', since: null }))
    const invitations = data.invitations.map((i): NeverRow => ({
        id: `convite-${i.id}`,
        name: i.email,
        email: i.email,
        status: 'Convite pendente',
        since: i.created_at,
    }))
    return [...members, ...invitations].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'))
}

export const filterNever = (rows: NeverRow[], actor: string): NeverRow[] =>
    rows.filter((r) => !actor || r.name === actor)

export const neverCsv = (rows: NeverRow[]): string =>
    toCsv(
        [
            { key: 'name', label: 'Quem' },
            { key: 'email', label: 'E-mail' },
            { key: 'status', label: 'Situação' },
            { key: 'since', label: 'Convidado em' },
        ],
        rows.map((r) => ({ ...r, since: r.since ? fullWhen(r.since) : '' })),
    )
