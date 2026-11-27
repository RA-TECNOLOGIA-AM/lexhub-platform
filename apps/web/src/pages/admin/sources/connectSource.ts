import type { IconName } from '../../../components/ui/Icon.tsx'
import type { DatabaseConnector, DataSource, ProductKey, ProductOffice, SourceCheck } from '../../../types/index.ts'

// Módulo: as regras do Conectar fonte, sem React (testadas em connectSource.test.ts).

export type ConnectorKey = ProductKey | 'postgres' | 'mysql' | 'sheets' | 'facebook_ads'

// Os tipos do primeiro passo, nesta ordem. secret = guarda senha, link ou token cifrado (precisa da chave na API).
// Tipo novo = uma linha aqui (e o passo dele no ConnectSourceDialog).
export const CONNECTORS: { key: ConnectorKey; label: string; hint: string; icon: IconName; secret: boolean }[] = [
    { key: 'lexpre', label: 'LexPre', hint: 'Escolha o escritório no banco do LexPre.', icon: 'db', secret: false },
    {
        key: 'lexflow',
        label: 'LexFlow',
        hint: 'Escolha o escritório no banco do LexFlow.',
        icon: 'flow',
        secret: false,
    },
    { key: 'postgres', label: 'Postgres', hint: 'Banco próprio da operação.', icon: 'db', secret: true },
    { key: 'mysql', label: 'MySQL', hint: 'Banco próprio da operação.', icon: 'db', secret: true },
    { key: 'sheets', label: 'Google Planilhas', hint: 'Planilha publicada na Web.', icon: 'sheet', secret: true },
    {
        key: 'facebook_ads',
        label: 'Facebook Ads',
        hint: 'Anúncios da conta na Meta, guardados por dia.',
        icon: 'target',
        secret: true,
    },
]

// ID da conta de anúncios como a API aceita: 'act_123', '123' ou com espaços. Fora disso, null.
export function normalizeAdAccount(raw: string): string | null {
    const m = /^(?:act_)?(\d{1,20})$/.exec(raw.replace(/\s+/g, ''))
    return m ? `act_${m[1]}` : null
}

export const isProduct = (key: ConnectorKey): key is ProductKey => key === 'lexpre' || key === 'lexflow'
export const isDatabase = (key: ConnectorKey): key is DatabaseConnector => key === 'postgres' || key === 'mysql'

// Por que um tipo não pode ser escolhido nesta unidade (null = pode).
// secretsReady = a API tem a chave que cifra senha e link (GET /sources/connect-info).
export function connectorBlock(
    key: ConnectorKey,
    needsSecret: boolean,
    sources: DataSource[],
    secretsReady: boolean,
): string | null {
    if (needsSecret && !secretsReady) return 'Falta configurar a chave de cifra na API'
    if (isProduct(key) && sources.some((s) => s.id === key)) return 'Já ligado a esta unidade'
    return null
}

// As checagens que falharam por erro (aviso não conta). Vazio = passou.
export const failedChecks = (checks: SourceCheck[]): SourceCheck[] =>
    checks.filter((c) => !c.skipped && !c.ok && c.severity === 'error')

// Os livres primeiro (por nome); os já ligados no fim, bloqueados.
export const sortOffices = (offices: ProductOffice[]): ProductOffice[] =>
    [...offices].sort(
        (a, b) => Number(a.linkedTo !== null) - Number(b.linkedTo !== null) || a.name.localeCompare(b.name, 'pt-BR'),
    )

// A linha de baixo de cada escritório: '128 movimentações nos últimos 30 dias' ou 'Ligado à unidade NG (LexGroup)'.
export function officeSub(office: ProductOffice, activityLabel: string): string {
    if (office.linkedTo) return `Ligado à unidade ${office.linkedTo.unit} (${office.linkedTo.org})`
    return `${office.activity.toLocaleString('pt-BR')} ${activityLabel}`
}
