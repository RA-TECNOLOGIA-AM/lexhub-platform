import type { AuditEvent, AuditKind, AuditQuery, MembersResponse } from '../../../types/index.ts'
import { toCsv, type CsvColumn } from '../../../lib/csv.ts'

// Nome no filtro "Tipo de evento" e cor do selo de cada tipo.
export const KIND: Record<AuditKind, { label: string; badge: string }> = {
    login: { label: 'Entradas', badge: 'badge neutral' },
    view: { label: 'Dashboards abertos', badge: 'badge info' },
    export: { label: 'Exportações', badge: 'badge info' },
    access: { label: 'Mudanças de acesso', badge: 'badge neutral' },
    account: { label: 'Segurança da conta', badge: 'badge off' },
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

// --- Filtros (Período, Tipo de evento, Pessoa) ---
// 'nunca' = "Nunca acessou": não é um evento, é quem nunca entrou (a tela troca para a lista de pessoas).
export const NEVER = 'nunca'
export const NEVER_LABEL = 'Nunca acessou'
// Período: últimos 7/30/90 dias ou datas livres (de/ate = 'AAAA-MM-DD', só valem em 'custom').
export const PERIODS = {
    '7': 'Últimos 7 dias',
    '30': 'Últimos 30 dias',
    '90': 'Últimos 90 dias',
    custom: 'Escolher datas',
}
export type AuditPeriod = keyof typeof PERIODS
export type AuditFilter = {
    kind: AuditKind | typeof NEVER | '' // '' = todos
    actor: string // '' = todas
    unit: string // código da unidade; '' = todas
    org: string // organização auditada (só a plataforma troca); '' = a da URL
    period: AuditPeriod
    de: string
    ate: string
}

export const filterEvents = (events: AuditEvent[], f: AuditFilter): AuditEvent[] =>
    events.filter((e) => (!f.kind || e.kind === f.kind) && (!f.actor || e.actor === f.actor))

const ISO_DAY = /^\d{4}-\d{2}-\d{2}$/
const DAY_MS = 24 * 60 * 60 * 1000
// Fuso da LexGroup (Manaus não tem horário de verão): as datas livres valem do começo ao fim do dia aqui.
const MANAUS_OFFSET = '-04:00'

// Filtro <-> URL (?periodo=&de=&ate=&tipo=&pessoa=). Valor desconhecido na URL vira o padrão
// (tipo: todos; período: 7 dias, que nem aparece na URL). Datas trocadas ou inválidas também voltam a 7 dias.
export function filterFromParams(params: URLSearchParams): AuditFilter {
    const kind = params.get('tipo') ?? ''
    const known = kind === NEVER || kind in KIND
    const period = params.get('periodo') ?? '7'
    const de = params.get('de') ?? ''
    const ate = params.get('ate') ?? ''
    const datesOk = ISO_DAY.test(de) && ISO_DAY.test(ate) && de <= ate
    const valid = period in PERIODS && (period !== 'custom' || datesOk)
    return {
        kind: known ? (kind as AuditFilter['kind']) : '',
        actor: params.get('pessoa') ?? '',
        unit: (params.get('unidade') ?? '').toUpperCase(),
        org: (params.get('org') ?? '').toLowerCase(),
        period: valid ? (period as AuditPeriod) : '7',
        de: valid && period === 'custom' ? de : '',
        ate: valid && period === 'custom' ? ate : '',
    }
}

export function paramsFromFilter(f: AuditFilter): URLSearchParams {
    const params = new URLSearchParams()
    if (f.period !== '7') params.set('periodo', f.period)
    if (f.period === 'custom') {
        params.set('de', f.de)
        params.set('ate', f.ate)
    }
    if (f.kind) params.set('tipo', f.kind)
    if (f.actor) params.set('pessoa', f.actor)
    if (f.unit) params.set('unidade', f.unit)
    if (f.org) params.set('org', f.org)
    return params
}

// '2026-11-30' -> '2026-12-01' (o dia seguinte, para o fim do "até" incluir o dia inteiro).
const nextDay = (day: string): string => new Date(Date.parse(`${day}T00:00:00Z`) + DAY_MS).toISOString().slice(0, 10)

// "Escolher datas" começa nos últimos 7 dias (o dia de hoje em Manaus), para a URL já nascer válida.
export function customRange(now = new Date()): { de: string; ate: string } {
    const day = (d: Date) => d.toLocaleDateString('sv-SE', { timeZone: 'America/Manaus' })
    return { de: day(new Date(now.getTime() - 7 * DAY_MS)), ate: day(now) }
}

// O que pedir ao banco: o período vira instantes; "Nunca acessou" não é um tipo de evento (busca todos).
export function queryFromFilter(f: AuditFilter, now = new Date()): AuditQuery {
    const kind = f.kind === NEVER ? '' : f.kind
    const { actor, unit } = f
    if (f.period === 'custom') {
        return {
            from: `${f.de}T00:00:00${MANAUS_OFFSET}`,
            to: `${nextDay(f.ate)}T00:00:00${MANAUS_OFFSET}`,
            kind,
            actor,
            unit,
        }
    }
    return { from: new Date(now.getTime() - Number(f.period) * DAY_MS).toISOString(), to: null, kind, actor, unit }
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
