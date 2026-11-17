import type {
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

// Conectar banco próprio e planilha no mock, com as mesmas regras da API (app/routes/source_connections.py):
// o teste nunca é erro (saved/ok + checagens), senha e link nunca voltam. Para treinar os caminhos:
//   host interno (localhost, 10.x, 192.168.x) = rede recusada; senha 'errada' = login recusado;
//   usuário postgres/root/admin = pode escrever (pede "Salvar mesmo assim"); link sem docs.google.com = inválido.

export const EGRESS_IP_EXEMPLO = '203.0.113.10'
const TABS: SheetTab[] = [
    { name: 'FINANCEIRO', rows: 1240 },
    { name: 'METAS', rows: 12 },
]

// Fonte conectada pela tela: guardamos a config (sem segredo) e um segredo fictício só para o mock.
type Stored = { config: Record<string, unknown>; secret: string; writerAck: boolean }
const stored = new Map<string, Stored>()

export const isManaged = (sourceId: string) => stored.has(sourceId)
export const managedConfig = (sourceId: string) => stored.get(sourceId)

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
    } else {
        const port = input.port ?? (input.connector === 'postgres' ? 5432 : 3306)
        ;({ checks, canWrite } = dbChecks(input.host, port, input.database, input.user, input.password, input.ssl))
    }
    if (!okOf(checks)) return { saved: false, needsWriterAck: false, checks, source: null }
    if (canWrite && input.connector !== 'sheets' && !input.writerAck) {
        return { saved: false, needsWriterAck: true, checks, source: null }
    }
    const prefix = input.connector === 'postgres' ? 'pg' : input.connector === 'mysql' ? 'my' : 'gs'
    const id = `${prefix}_${unitCode.toLowerCase().replace(/[^a-z0-9]/g, '')}_${(++seq).toString(16).padStart(6, '0')}`
    const source: DataSource = {
        id,
        connector: input.connector,
        kind: input.connector === 'sheets' ? 'sheet' : 'database',
        group: 'connection',
        name: input.name.trim(),
        detail:
            input.connector === 'sheets'
                ? `Google Planilhas · aba ${input.tab}`
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
                : {
                      host: input.host,
                      port: input.port ?? (input.connector === 'postgres' ? 5432 : 3306),
                      database: input.database,
                      user: input.user,
                      ssl: input.ssl,
                  },
        secret: input.connector === 'sheets' ? input.url : input.password,
        writerAck: canWrite,
    })
    unit.sources.push(source)
    return { saved: true, needsWriterAck: false, checks, source }
}

function managed(sourceId: string): Stored {
    const s = stored.get(sourceId)
    if (!s)
        throw new DataError(
            409,
            'Esta fonte não é gerenciada pela tela (produto Lex, banco interno ou planilha antiga).',
        )
    return s
}

function runChecks(s: Stored, secret: string) {
    const c = s.config
    if ('tab' in c) return { checks: sheetChecks(secret, String(c.tab)), canWrite: false }
    return dbChecks(String(c.host), Number(c.port), String(c.database), String(c.user), secret, Boolean(c.ssl))
}

export function retestIn(sourceId: string): SourceTestResult {
    const s = managed(sourceId)
    const { checks } = runChecks(s, s.secret)
    return { ok: okOf(checks), checks }
}

export function changeSecretIn(data: SourcesResponse, sourceId: string, input: SecretInput): ConnectResult {
    const s = managed(sourceId)
    const secret = 'tab' in s.config ? input.url : input.password
    if (!secret) throw new DataError(422, 'Informe a nova senha (ou o novo link).')
    const { checks, canWrite } = runChecks(s, secret)
    if (!okOf(checks)) return { saved: false, needsWriterAck: false, checks, source: null }
    if (canWrite && !input.writerAck) return { saved: false, needsWriterAck: true, checks, source: null }
    s.secret = secret
    s.writerAck = canWrite
    const source = data.units.flatMap((u) => u.sources).find((x) => x.id === sourceId) ?? null
    return { saved: true, needsWriterAck: false, checks, source }
}

export function disconnectIn(data: SourcesResponse, sourceId: string): void {
    managed(sourceId)
    stored.delete(sourceId)
    for (const u of data.units) u.sources = u.sources.filter((s) => s.id !== sourceId)
}
