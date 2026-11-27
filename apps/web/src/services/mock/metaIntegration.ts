import { DataError } from '../errors.ts'
import type {
    MetaIntegration,
    MetaIntegrationInput,
    MetaIntegrationSaved,
    MetaIntegrationTest,
    SourceCheck,
} from '../../types/index.ts'

const VERSIONS = ['v24.0', 'v25.0', 'v26.0']
const DEFAULT_VERSION = 'v26.0'
const INTERVALS = [5, 10, 15, 30, 60]

const check = (key: SourceCheck['key'], ok: boolean, message: string): SourceCheck => ({
    key,
    ok,
    message,
    ms: 180,
    severity: 'error',
    skipped: false,
})

// O teste do app no mock: chave com "errado" = a Meta recusa; o resto passa.
function testApp(appId: string, secret: string, version: string): MetaIntegrationTest {
    if (secret.includes('errado')) {
        return {
            ok: false,
            app: null,
            checks: [
                check('network', true, 'A API alcançou graph.facebook.com'),
                check(
                    'login',
                    false,
                    `A Meta recusou o ID e a chave do app na versão ${version} (código 190). Confira em ` +
                        'developers.facebook.com > seu app > Configurações do app > Básico.',
                ),
            ],
        }
    }
    return {
        ok: true,
        app: 'LexHub Ads',
        checks: [
            check('network', true, 'A API alcançou graph.facebook.com'),
            check('login', true, `App LexHub Ads (${appId}) aceito pela Meta na versão ${version}`),
        ],
    }
}

// Módulo: a Integração Meta no modo mock, com as mesmas regras da API (app/routes/integrations_routes.py):
// a chave nunca volta, chave nova (ou ID novo com a chave salva) é testada antes e teste que falha não grava.
// Em memória: o F5 volta ao começo (sem app, como um servidor novo).
export function createMockMetaIntegration() {
    let appId: string | null = null
    let secret: string | null = null
    let graphVersion: string | null = null
    let syncPaused = false
    let syncInterval: number | null = null
    let updatedAt: string | null = null
    let updatedBy: string | null = null

    function get(): MetaIntegration {
        const version = graphVersion ?? DEFAULT_VERSION
        return {
            appId,
            hasAppSecret: secret !== null,
            secretUnreadable: false,
            graphVersion: version,
            versions: VERSIONS.includes(version) ? VERSIONS : [...VERSIONS, version],
            syncPaused,
            syncIntervalMin: syncInterval ?? 10,
            intervals: INTERVALS,
            syncAvailable: true,
            origin: {
                appId: appId ? 'tela' : 'nenhum',
                appSecret: secret ? 'tela' : 'nenhum',
                graphVersion: graphVersion ? 'tela' : 'padrão',
                syncInterval: syncInterval ? 'tela' : 'padrão',
            },
            updatedAt,
            updatedBy,
        }
    }

    function test(input: { appId: string; appSecret: string | null; graphVersion: string }): MetaIntegrationTest {
        const key = input.appSecret?.trim() || secret
        if (!key) {
            return {
                ok: false,
                app: null,
                checks: [check('login', false, 'Informe a chave secreta do app (Configurações do app > Básico).')],
            }
        }
        return testApp(input.appId, key, input.graphVersion)
    }

    function save(input: MetaIntegrationInput, who: string): MetaIntegrationSaved {
        const id = input.appId.trim()
        if (id && !/^\d{5,25}$/.test(id)) throw new DataError(422, 'O ID do app tem só números.')
        if (!INTERVALS.includes(input.syncIntervalMin)) {
            throw new DataError(422, 'Intervalo da atualização: 5, 10, 15, 30 ou 60 minutos.')
        }
        const fresh = input.appSecret?.trim() ?? ''
        let action: 'keep' | 'set' | 'clear' = input.appSecret === null ? 'keep' : fresh ? 'set' : 'clear'
        if (!id && action !== 'clear' && secret) action = 'clear' // sem app, a chave não serve para nada
        if (action === 'set' && !id) throw new DataError(422, 'Informe o ID do app junto com a chave.')

        let toTest = action === 'set' ? fresh : ''
        if (action === 'keep' && id && id !== appId && secret) toTest = secret
        let checks: SourceCheck[] = []
        if (toTest) {
            const result = testApp(id, toTest, input.graphVersion)
            checks = result.checks
            if (!result.ok) return { saved: false, checks, integration: get() }
        }

        appId = id || null
        if (action === 'set') secret = fresh
        if (action === 'clear') secret = null
        graphVersion = input.graphVersion
        syncPaused = input.syncPaused
        syncInterval = input.syncIntervalMin
        updatedAt = new Date().toISOString()
        updatedBy = who
        return { saved: true, checks, integration: get() }
    }

    return { get, test, save }
}
