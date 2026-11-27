import type { ApiKeyInfo } from '../../../types/index.ts'

export type ApiKeysTab = 'pending' | 'active' | 'closed'

export const TABS: { id: ApiKeysTab; label: string; empty: string }[] = [
    { id: 'pending', label: 'Pendentes', empty: 'Nenhum pedido pendente.' },
    { id: 'active', label: 'Ativas', empty: 'Nenhuma chave ativa.' },
    { id: 'closed', label: 'Encerradas', empty: 'Nenhuma chave recusada ou revogada.' },
]

// Os setores extras ainda sem decisão (o Desenvolvedor marca quais aprova; começam todos marcados).
export function pendingExtras(key: ApiKeyInfo): string[] {
    return key.sectors.filter((s) => !s.base && s.status === 'pending').map((s) => s.setor)
}

export const fmtDateTime = (iso: string | null) => (iso ? new Date(iso).toLocaleString('pt-BR') : '—')
