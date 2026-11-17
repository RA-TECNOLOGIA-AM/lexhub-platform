// Módulo: barra lateral recolhida (só ícones) ou aberta, sem React (testado em sidebar.test.ts).
// A escolha fica no localStorage e volta igual no F5. Valor estranho ou storage bloqueado = aberta.

export const SIDEBAR_KEY = 'lexhub.sidebar'

export function storedSidebarCollapsed(storage: Pick<Storage, 'getItem'> | null = safeLocal()): boolean {
    try {
        return storage?.getItem(SIDEBAR_KEY) === 'collapsed'
    } catch {
        return false
    }
}

export function storeSidebarCollapsed(
    collapsed: boolean,
    storage: Pick<Storage, 'setItem'> | null = safeLocal(),
): void {
    try {
        storage?.setItem(SIDEBAR_KEY, collapsed ? 'collapsed' : 'expanded')
    } catch {
        // sem storage: vale só enquanto a página estiver aberta
    }
}

function safeLocal(): Storage | null {
    try {
        return window.localStorage
    } catch {
        return null
    }
}
