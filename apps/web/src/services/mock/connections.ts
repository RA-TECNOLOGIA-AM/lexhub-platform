import type {
    AdsOptions,
    AdsPreview,
    AdsSettings,
    AdsSettingsSaved,
    AdsSummary,
    AdsTokenInfo,
    ConnectInput,
    ConnectResult,
    DataSource,
    SecretInput,
    SheetTab,
    SourceCheck,
    SourcesResponse,
    SourceTestResult,
} from '../../types/index.ts'
import { DataError } from '../errors.ts'
import { CONVERSATION, adsAccountName, adsOptions, adsPreview, adsSummary, adsTokenInfo } from './facebookAds.ts'

// Conectar banco próprio e planilha no mock, com as mesmas regras da API (app/routes/source_connections.py):
// o teste nunca é erro (saved/ok + checagens), senha e link nunca voltam. Para treinar os caminhos:
//   host interno (localhost, 10.x, 192.168.x) = rede recusada; senha 'errada' = login recusado;
//   usuário postgres/root/admin = pode escrever (pede "Salvar mesmo assim"); link sem docs.google.com = inválido;
//   Facebook Ads: token com 'errado' = recusado pela Meta; conta terminada em 0 = desativada (aviso, salva mesmo assim).

export const EGRESS_IP_EXEMPLO = '203.0.113.10'
const TABS: SheetTab[] = [
    { name: 'FINANCEIRO', rows: 1240 },
    { name: 'METAS', rows: 12 },
]

// Fonte com o segredo no banco: guardamos a config (sem segredo), um segredo fictício só para o mock,
// se está ligada, o status de antes de desligar e a estrutura salva no teste (detalhe técnico).
type Stored = {
    connectedAt?: number // Facebook Ads: quando a coleta (fictícia) do histórico começou
    config: Record<string, unknown>
    secret: string
    writerAck: boolean
    enabled: boolean
    statusBefore: DataSource['status'] | null
    schema: Record<string, [string, string][]> | null
}
const LEGACY_SCHEMA: Record<string, [string, string][]> = {
    'REPASSES CLIENTES': [
        ['DATA DO TED', ''],
        ['CLIENTE', ''],
        ['HONO', ''],
    ],
}
// As planilhas antigas (link levado do .env para o banco pelo script do PR 3): planilha inteira (config {}).
const stored = new Map<string, Stored>(
    ['sheets_financeiro_ng', 'sheets_financeiro_la'].map((id) => [
        id,
        {
            config: {},
            secret: 'https://docs.google.com/spreadsheets/d/e/exemplo/pub?output=xlsx',
            writerAck: false,
            enabled: true,
            statusBefore: null,
            schema: LEGACY_SCHEMA,
        },
    ]),
)

export const isManaged = (sourceId: string) => stored.has(sourceId)
export const isDisabled = (sourceId: string) => stored.get(sourceId)?.enabled === false

// Dashboards do mock que leem uma planilha antiga (como na API: Meta anual e Financeiro estratégico).
const SHEET_OF_UNIT: Record<string, string> = { NG: 'sheets_financeiro_ng', LA_AM: 'sheets_financeiro_la' }
const SHEET_DASHBOARDS = new Set(['meta-anual', 'financeiro-estrategico'])

// Como a casca da API: fonte desligada pela TI = 423 "Fonte desligada" (não é erro de integração).
export function requireSourceOn(dashboardKey: string, unit: string): void {
    const sheet = SHEET_DASHBOARDS.has(dashboardKey) ? SHEET_OF_UNIT[unit] : undefined
    if (sheet && isDisabled(sheet)) throw new DataError(423, 'A fonte Planilha do financeiro está desligada')
}
export const managedConfig = (sourceId: string) => stored.get(sourceId)

const DB_SCHEMA: Record<string, [string, string][]> = {
    'public.processo': [
        ['id', 'integer'],
        ['numero', 'text'],
        ['cliente_id', 'integer'],
        ['criado_em', 'timestamp with time zone'],
    ],
    'public.cliente': [
        ['id', 'integer'],
        ['nome', 'text'],
    ],
}

const check = (
    key: SourceCheck['key'],
    ok: boolean,
    message: string,
    severity: SourceCheck['severity'] = 'error',
): SourceCheck => ({
    key,
    ok,
    message,
    ms: 40 + Math.round(Math.random() * 120),
    severity,
    skipped: false,
})

function stop(checks: SourceCheck[]): SourceCheck[] {
    const labels: [SourceCheck['key'], string][] = [
        ['network', 'Rede'],
        ['login', 'Login'],
        ['read', 'Leitura'],
        ['readOnly', 'Só leitura'],
    ]
    for (const [key, label] of labels) {
        if (!checks.some((c) => c.key === key)) {
            checks.push({ key, ok: false, message: `${label}: não testado`, ms: 0, severity: 'error', skipped: true })
        }
    }
    return checks
}

const okOf = (checks: SourceCheck[]) => checks.every((c) => c.skipped || c.ok || c.severity === 'warn')

function dbChecks(host: string, port: number, database: string, user: string, password: string, ssl: boolean) {
    if (/^(localhost|127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(host) || port < 1024) {
        return {
            checks: stop([
                check(
                    'network',
                    false,
                    'Este endereço é de rede interna ou usa porta de sistema. Use o endereço público do banco (porta 1024 ou maior).',
                ),
            ]),
            canWrite: false,
        }
    }
    const checks = [check('network', true, `A API alcançou ${host}:${port}`)]
    if (password === 'errada') {
        return {
            checks: stop([
                ...checks,
                check('login', false, 'Usuário ou senha recusados pelo banco. Confira e teste de novo.'),
            ]),
            canWrite: false,
        }
    }
    checks.push(check('login', true, `Entrou no banco ${database} ${ssl ? 'com SSL' : 'sem SSL'}`))
    checks.push(check('read', true, '42 tabelas encontradas'))
    const canWrite = /^(postgres|root|admin|sa)$/i.test(user)
    checks.push(
        canWrite
            ? check(
                  'readOnly',
                  false,
                  `O usuário ${user} pode alterar dados. Recomendamos um usuário só de leitura (passo 1).`,
                  'warn',
              )
            : check('readOnly', true, 'O usuário não tem permissão de escrita'),
    )
    return { checks, canWrite }
}

function sheetChecks(url: string, tab: string | null): SourceCheck[] {
    if (!/^https:\/\/docs\.google\.com\/spreadsheets\/d\//.test(url.trim())) {
        return [
            check(
                'network',
                false,
                'Link inválido. Use o link de "Publicar na Web" (ou de compartilhamento) da planilha.',
            ),
        ]
    }
    const checks = [check('network', true, `Planilha baixada: ${TABS.length} abas`)]
    if (tab !== null) {
        const found = TABS.find((t) => t.name === tab)
        checks.push(
            found
                ? check('read', true, `Aba ${tab}: ${found.rows} linhas`)
                : check('read', false, `A aba ${tab} não existe nessa planilha.`),
        )
    }
    return checks
}

// O que a coleta do Facebook Ads grava, para o detalhe técnico da fonte (como app/facebook_ads.py).
const ADS_SCHEMA: Record<string, [string, string][]> = {
    'app.facebook_ads_daily': [
        ['day', 'date'],
        ['ad_id', 'text'],
        ['ad_name', 'text'],
        ['campaign_name', 'text'],
        ['spend', 'numeric'],
        ['impressions', 'bigint'],
        ['link_clicks', 'bigint'],
        ['landing_page_views', 'bigint'],
        ['leads', 'bigint'],
        ['conversations', 'bigint'],
        ['results', 'numeric'],
        ['reach', 'bigint'],
        ['actions', 'jsonb'],
    ],
    'app.facebook_ads_breakdowns': [
        ['day', 'date'],
        ['breakdown', 'text'],
        ['campaign_id', 'text'],
        ['dim1', 'text'],
        ['dim2', 'text'],
        ['spend', 'numeric'],
        ['results', 'numeric'],
    ],
    'app.facebook_ads_entities': [
        ['level', 'text'],
        ['id', 'text'],
        ['name', 'text'],
        ['effective_status', 'text'],
        ['objective', 'text'],
        ['daily_budget', 'numeric'],
        ['creative', 'jsonb'],
    ],
}

const adAccount = (raw: string): string | null => {
    const m = /^(?:act_)?(\d{1,20})$/.exec(raw.replace(/\s+/g, ''))
    return m ? `act_${m[1]}` : null
}

const skipped = (key: SourceCheck['key'], label: string): SourceCheck => ({
    key,
    ok: false,
    message: `${label}: não testado`,
    ms: 0,
    severity: 'error',
    skipped: true,
})

function adsChecks(account: string, token: string): SourceCheck[] {
    const id = adAccount(account)
    if (!id) {
        return [
            check(
                'read',
                false,
                'ID da conta inválido. Use act_ seguido dos números (Gerenciador de Anúncios > Configurações da conta).',
            ),
        ]
    }
    const checks = [check('network', true, 'A API alcançou graph.facebook.com')]
    if (token.includes('errado')) {
        return [
            ...checks,
            check(
                'login',
                false,
                'A Meta recusou o token (inválido, expirado ou revogado). Gere um novo token do usuário do sistema.',
            ),
            skipped('read', 'Leitura'),
            skipped('account', 'Conta'),
        ]
    }
    checks.push(check('login', true, 'Token aceito pela Meta (usuário Coletor LexHub)'))
    checks.push(
        check('read', true, `Conta ${adsAccountName(id)}: BRL 1.234,56 gastos e 98.765 impressões nos últimos 7 dias`),
    )
    checks.push(
        id.endsWith('0')
            ? check(
                  'account',
                  false,
                  'A conta está desativada: a coleta traz o histórico, mas não há anúncios novos.',
                  'warn',
              )
            : check('account', true, 'Conta de anúncios ativa'),
    )
    return checks
}

export function inspectSheetIn(url: string): SheetTab[] {
    const checks = sheetChecks(url, null)
    if (!okOf(checks)) throw new DataError(422, checks[0].message)
    return TABS.map((t) => ({ ...t }))
}

let seq = 0

export function connectIn(data: SourcesResponse, unitCode: string, input: ConnectInput): ConnectResult {
    const unit = data.units.find((u) => u.unit.code === unitCode)
    if (!unit) throw new DataError(404, 'Unidade não encontrada')
    let checks: SourceCheck[]
    let canWrite = false
    if (input.connector === 'sheets') {
        checks = sheetChecks(input.url, input.tab)
    } else if (input.connector === 'facebook_ads') {
        checks = adsChecks(input.adAccountId, input.token)
    } else {
        const port = input.port ?? (input.connector === 'postgres' ? 5432 : 3306)
        ;({ checks, canWrite } = dbChecks(input.host, port, input.database, input.user, input.password, input.ssl))
    }
    if (!okOf(checks)) return { saved: false, needsWriterAck: false, checks, source: null }
    if (canWrite && input.connector !== 'sheets' && input.connector !== 'facebook_ads' && !input.writerAck) {
        return { saved: false, needsWriterAck: true, checks, source: null }
    }
    const prefix = { postgres: 'pg', mysql: 'my', sheets: 'gs', facebook_ads: 'fb' }[input.connector]
    const account = input.connector === 'facebook_ads' ? (adAccount(input.adAccountId) ?? '') : ''
    const id = `${prefix}_${unitCode.toLowerCase().replace(/[^a-z0-9]/g, '')}_${(++seq).toString(16).padStart(6, '0')}`
    const source: DataSource = {
        id,
        connector: input.connector,
        kind: input.connector === 'sheets' ? 'sheet' : input.connector === 'facebook_ads' ? 'ads' : 'database',
        group: 'connection',
        name: input.name.trim(),
        detail:
            input.connector === 'sheets'
                ? `Google Planilhas · aba ${input.tab}`
                : input.connector === 'facebook_ads'
                  ? `Facebook Ads · ${adsAccountName(account)} (${account})`
                  : `${input.connector === 'postgres' ? 'Postgres' : 'MySQL'} · ${input.host}/${input.database}`,
        managedBy: null,
        syncedAt: null,
        rows: null,
        failures: 0,
        status: 'no_dashboards',
    }
    stored.set(id, {
        config:
            input.connector === 'sheets'
                ? { tab: input.tab }
                : input.connector === 'facebook_ads'
                  ? {
                        ad_account_id: account,
                        account_name: adsAccountName(account),
                        currency: 'BRL',
                        timezone: 'America/Manaus',
                        ...adsConfig(input.settings, 1),
                    }
                  : {
                        host: input.host,
                        port: input.port ?? (input.connector === 'postgres' ? 5432 : 3306),
                        database: input.database,
                        user: input.user,
                        ssl: input.ssl,
                    },
        secret:
            input.connector === 'sheets'
                ? input.url
                : input.connector === 'facebook_ads'
                  ? input.token
                  : input.password,
        writerAck: canWrite,
        enabled: true,
        statusBefore: null,
        connectedAt: Date.now(),
        schema:
            input.connector === 'facebook_ads'
                ? ADS_SCHEMA
                : input.connector === 'sheets'
                  ? Object.fromEntries(
                        TABS.map((t) => [
                            t.name,
                            [
                                ['DATA', ''],
                                ['VALOR', ''],
                            ],
                        ]),
                    )
                  : DB_SCHEMA,
    })
    unit.sources.push(source)
    return { saved: true, needsWriterAck: false, checks, source }
}

function managed(sourceId: string): Stored {
    const s = stored.get(sourceId)
    if (!s) throw new DataError(409, 'Esta fonte não é gerenciada pela tela (produto Lex ou banco interno).')
    return s
}

const isSheetConfig = (c: Record<string, unknown>) => 'tab' in c || Object.keys(c).length === 0
const isAdsConfig = (c: Record<string, unknown>) => 'ad_account_id' in c

function runChecks(s: Stored, secret: string) {
    const c = s.config
    if (isAdsConfig(c)) return { checks: adsChecks(String(c.ad_account_id), secret), canWrite: false }
    if (isSheetConfig(c)) return { checks: sheetChecks(secret, 'tab' in c ? String(c.tab) : null), canWrite: false }
    return dbChecks(String(c.host), Number(c.port), String(c.database), String(c.user), secret, Boolean(c.ssl))
}

export function retestIn(sourceId: string): SourceTestResult {
    const s = managed(sourceId)
    const { checks } = runChecks(s, s.secret)
    return { ok: okOf(checks), checks }
}

export function changeSecretIn(data: SourcesResponse, sourceId: string, input: SecretInput): ConnectResult {
    const s = managed(sourceId)
    const secret = isAdsConfig(s.config) ? input.token : isSheetConfig(s.config) ? input.url : input.password
    if (!secret) throw new DataError(422, 'Informe a nova senha (ou o novo link ou token).')
    const { checks, canWrite } = runChecks(s, secret)
    if (!okOf(checks)) return { saved: false, needsWriterAck: false, checks, source: null }
    if (canWrite && !input.writerAck) return { saved: false, needsWriterAck: true, checks, source: null }
    s.secret = secret
    s.writerAck = canWrite
    const source = data.units.flatMap((u) => u.sources).find((x) => x.id === sourceId) ?? null
    return { saved: true, needsWriterAck: false, checks, source }
}

export function disconnectIn(data: SourcesResponse, sourceId: string): void {
    const s = managed(sourceId)
    if (Object.keys(s.config).length === 0) {
        throw new DataError(409, 'Esta planilha é usada pelo código dos dashboards: desligue em vez de desconectar.')
    }
    stored.delete(sourceId)
    for (const u of data.units) u.sources = u.sources.filter((x) => x.id !== sourceId)
}

// Ligar/desligar (pausa): o segredo fica; desligada = status 'disabled' em todas as unidades que a usam.
export function setEnabledIn(data: SourcesResponse, sourceId: string, enabled: boolean): DataSource {
    const s = managed(sourceId)
    const rows = data.units.flatMap((u) => u.sources).filter((x) => x.id === sourceId)
    if (rows.length === 0) throw new DataError(404, 'Fonte não encontrada')
    if (s.enabled !== enabled) {
        if (!enabled) s.statusBefore = rows[0].status
        for (const row of rows) row.status = enabled ? (s.statusBefore ?? 'waiting') : 'disabled'
        s.enabled = enabled
    }
    return rows[0]
}

// --- Facebook Ads: token, opções da conta, prévia e personalização (app/routes/facebook_ads_routes.py) ---

// A personalização na config (snake_case, como app/facebook_ads.py) e de volta.
function adsConfig(settings: AdsSettings, collectVersion: number): Record<string, unknown> {
    return {
        metrics: [...settings.metrics],
        conversions: [...settings.conversions],
        campaigns: settings.campaigns ? [...settings.campaigns] : null,
        breakdowns: [...settings.breakdowns],
        backfill_days: settings.backfillDays,
        creatives: settings.creatives,
        collect_version: collectVersion,
    }
}

function adsSettingsOf(c: Record<string, unknown>): AdsSettings {
    return {
        metrics: (c.metrics as AdsSettings['metrics']) ?? ['reach'],
        conversions: (c.conversions as string[]) ?? ['lead', CONVERSATION],
        campaigns: (c.campaigns as string[] | null) ?? null,
        breakdowns: (c.breakdowns as AdsSettings['breakdowns']) ?? [],
        backfillDays: (c.backfill_days as AdsSettings['backfillDays']) ?? 1095,
        creatives: c.creatives === undefined ? true : Boolean(c.creatives),
    }
}

function adsSource(sourceId: string): Stored {
    const s = managed(sourceId)
    if (!isAdsConfig(s.config)) throw new DataError(409, 'Só a fonte Facebook Ads tem personalização.')
    return s
}

export const readAdsTokenIn = (token: string): AdsTokenInfo => adsTokenInfo(token)

export function inspectAdsIn(input: { adAccountId: string; token: string }): AdsOptions {
    const checks = adsChecks(input.adAccountId, input.token)
    const account = adAccount(input.adAccountId)
    if (!okOf(checks) || !account) return { ok: false, checks, account: null, campaigns: [], conversions: [] }
    return {
        ok: true,
        checks,
        account: {
            id: account,
            name: adsAccountName(account),
            currency: 'BRL',
            timezone: 'America/Manaus',
            status: account.endsWith('0') ? 'desativada' : 'ativa',
        },
        ...adsOptions(),
    }
}

export function previewAdsIn(input: { adAccountId: string; settings: AdsSettings }): AdsPreview {
    if (!adAccount(input.adAccountId)) throw new DataError(422, 'ID da conta inválido.')
    return adsPreview(input.settings)
}

export function adsTokenSavedIn(sourceId: string): AdsTokenInfo {
    return adsTokenInfo(adsSource(sourceId).secret)
}

export function adsOptionsIn(sourceId: string): AdsOptions {
    const c = adsSource(sourceId).config
    return {
        ok: true,
        checks: [],
        account: {
            id: String(c.ad_account_id),
            name: String(c.account_name),
            currency: String(c.currency),
            timezone: String(c.timezone),
            status: null,
        },
        ...adsOptions(),
        settings: adsSettingsOf(c),
    }
}

export function previewSavedAdsIn(sourceId: string, settings: AdsSettings): AdsPreview {
    adsSource(sourceId)
    return adsPreview(settings)
}

export function saveAdsSettingsIn(data: SourcesResponse, sourceId: string, settings: AdsSettings): AdsSettingsSaved {
    const s = adsSource(sourceId)
    if (settings.conversions.length === 0) throw new DataError(422, 'Escolha ao menos uma conversão.')
    const before = adsSettingsOf(s.config)
    const same = (a: readonly string[] | null, b: readonly string[] | null) =>
        a === null || b === null ? a === b : a.length === b.length && a.every((x) => b.includes(x))
    const recollect =
        !same(before.metrics, settings.metrics) ||
        !same(before.campaigns, settings.campaigns) ||
        !same(before.breakdowns, settings.breakdowns) ||
        before.backfillDays !== settings.backfillDays
    const version = Number(s.config.collect_version ?? 1) + (recollect ? 1 : 0)
    s.config = { ...s.config, ...adsConfig(settings, version) }
    if (recollect) s.connectedAt = Date.now()
    const source = data.units.flatMap((u) => u.sources).find((x) => x.id === sourceId)
    if (!source) throw new DataError(404, 'Fonte não encontrada')
    return { source, recollect, settings }
}

// O resumo do que está guardado: o histórico fictício leva 1 minuto para "chegar" depois de conectar.
export function adsSummaryIn(sourceId: string): AdsSummary | null {
    const s = stored.get(sourceId)
    if (!s || !isAdsConfig(s.config)) return null
    const progress = (Date.now() - (s.connectedAt ?? 0)) / 60_000
    return adsSummary(adsSettingsOf(s.config), progress)
}
