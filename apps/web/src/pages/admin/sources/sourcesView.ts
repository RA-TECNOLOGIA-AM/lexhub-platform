import type { DataSource, SourceGroup, SourceStatus, UnitSources } from '../../../types/index.ts'
import { timeAgo } from '../../../lib/format.ts'

// Módulo: as regras de texto e cor da tela Unidades e fontes, sem React (testadas em sourcesView.test.ts).

// Texto do cabeçalho: o intervalo vem do servidor (o cache de 5 min), nunca fixo na tela.
export const syncNote = (minutes: number): string =>
    `As fontes são sincronizadas a cada ${minutes} minutos para a base central da organização. ` +
    'As credenciais ficam no cofre e nunca voltam para a tela.'

const SOURCE_STATUS: Record<SourceStatus, { label: string; badge: string }> = {
    healthy: { label: 'Saudável', badge: 'badge ok' },
    late: { label: 'Atrasada', badge: 'badge warn' },
    pending: { label: 'Autorizar', badge: 'badge info' },
    waiting: { label: 'Aguardando sync', badge: 'badge neutral' },
}

export const statusOf = (status: SourceStatus) => SOURCE_STATUS[status]

// Os dois grupos da lista, nesta ordem. Grupo novo = uma linha aqui.
const GROUPS: { group: SourceGroup; title: string; hint: string }[] = [
    { group: 'product', title: 'Produtos contratados', hint: 'Vêm do contrato da organização' },
    { group: 'connection', title: 'Fontes conectadas', hint: 'Bancos e planilhas conectados por uma unidade' },
]

export type SourceSection = { group: SourceGroup; title: string; hint: string; sources: DataSource[] }

// As fontes separadas em grupos; grupo sem fonte não aparece.
export const groupSources = (sources: DataSource[]): SourceSection[] =>
    GROUPS.map((g) => ({ ...g, sources: sources.filter((s) => s.group === g.group) })).filter(
        (g) => g.sources.length > 0,
    )

// A linha de baixo do nome: 'Postgres · somente leitura · gerenciada por NICOLAS GOMES' (fonte de outra unidade).
export const detailLabel = (source: DataSource): string =>
    source.managedBy ? `${source.detail} · gerenciada por ${source.managedBy}` : source.detail

// 'fonte' / 'fontes', 'falha' / 'falhas'...
const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`

// 18000 -> '18 mil', 1500 -> '1,5 mil', 950 -> '950'
const compact = new Intl.NumberFormat('pt-BR', { notation: 'compact' })
// O Intl separa '18' e 'mil' com espaço não separável (\u00A0); trocamos por espaço comum.
export const rowsLabel = (rows: number): string => `${compact.format(rows).replace(/\s/g, ' ')} linhas`
// A linha do meio de cada fonte: 'há 4 min · 18 mil linhas', 'há 3 h · 2 falhas seguidas', 'Ainda não autorizada'.
export function whenLabel(source: DataSource, now: number = Date.now()): string {
    if (source.syncedAt === null) return source.status === 'pending' ? 'Ainda não autorizada' : 'Nunca sincronizada'
    const parts = [timeAgo(source.syncedAt, now)]
    if (source.failures > 0) parts.push(plural(source.failures, 'falha seguida', 'falhas seguidas'))
    else if (source.rows !== null) parts.push(rowsLabel(source.rows))
    return parts.join(' · ')
}

// Texto embaixo do nome da unidade no menu: '5 fontes · America/Manaus'.
export const unitSub = (u: UnitSources): string => `${plural(u.sources.length, 'fonte', 'fontes')} · ${u.timezone}`

// Indicador "Última falha": 'LexPre: tempo esgotado (30 s)' ou 'Nenhuma nos últimos 7 dias'.
export const lastFailureLabel = (u: UnitSources): string =>
    u.lastFailure ? `${u.lastFailure.source}: ${u.lastFailure.message}` : 'Nenhuma nos últimos 7 dias'

// '3 de 5 unidades do plano'; null = o plano não limita (a linha some).
export const unitLimitLabel = (limit: { used: number; total: number } | null): string | null =>
    limit ? `${limit.used} de ${limit.total} unidades do plano` : null

// A unidade escolhida (vem da URL: ?unidade=LA_AM). Código inválido ou ausente = a primeira.
export const pickUnit = (units: UnitSources[], code: string | null): UnitSources | undefined =>
    units.find((u) => u.unit.code === code) ?? units[0]
