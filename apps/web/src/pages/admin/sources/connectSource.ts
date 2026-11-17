import type { IconName } from '../../../components/ui/Icon.tsx'
import type { DataSource, ProductKey, ProductOffice } from '../../../types/index.ts'

// Módulo: as regras do Conectar fonte, sem React (testadas em connectSource.test.ts).

export type ConnectorKey = ProductKey | 'postgres' | 'mysql' | 'sheets'

// Os tipos do primeiro passo, nesta ordem. ready = já dá para conectar nesta versão.
// Tipo novo = uma linha aqui (e o passo dele no ConnectSourceDialog).
export const CONNECTORS: { key: ConnectorKey; label: string; hint: string; icon: IconName; ready: boolean }[] = [
    { key: 'lexpre', label: 'LexPre', hint: 'Escolha o escritório no banco do LexPre.', icon: 'db', ready: true },
    { key: 'lexflow', label: 'LexFlow', hint: 'Escolha o escritório no banco do LexFlow.', icon: 'flow', ready: true },
    { key: 'postgres', label: 'Postgres', hint: 'Banco próprio da operação.', icon: 'db', ready: false },
    { key: 'mysql', label: 'MySQL', hint: 'Banco próprio da operação.', icon: 'db', ready: false },
    {
        key: 'sheets',
        label: 'Google Planilhas',
        hint: 'Planilha compartilhada com o LexHub.',
        icon: 'sheet',
        ready: false,
    },
]

export const isProduct = (key: ConnectorKey): key is ProductKey => key === 'lexpre' || key === 'lexflow'

// Por que um tipo não pode ser escolhido nesta unidade (null = pode).
export function connectorBlock(key: ConnectorKey, ready: boolean, sources: DataSource[]): string | null {
    if (!ready) return 'Em breve'
    if (isProduct(key) && sources.some((s) => s.id === key)) return 'Já ligado a esta unidade'
    return null
}

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
