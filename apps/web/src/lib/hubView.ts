// Módulo: como a pessoa vê o hub (lista em seções ou quadro em colunas), sem React (testado em hubView.test.ts).
// A escolha fica no localStorage deste navegador; sem escolha (ou storage bloqueado), vale a lista.

export type HubView = 'lista' | 'quadro'

export const HUB_VIEW_KEY = 'lexhub.hubView'

export function storedHubView(storage: Pick<Storage, 'getItem'> | null = safeLocal()): HubView {
    try {
        return storage?.getItem(HUB_VIEW_KEY) === 'quadro' ? 'quadro' : 'lista'
    } catch {
        return 'lista'
    }
}

export function storeHubView(view: HubView, storage: Pick<Storage, 'setItem'> | null = safeLocal()): void {
    try {
        storage?.setItem(HUB_VIEW_KEY, view)
    } catch {
        // sem storage: vale só enquanto a página estiver aberta
    }
}

// Cor de cada coluna do quadro (variáveis do tokens/app.css, que já mudam no tema escuro).
const AREA_COLORS: Record<string, string> = {
    Favoritos: 'var(--chart-brand)', // cor da marca, fixa (não segue a cor de destaque)
    Comercial: 'var(--pie-2)',
    'Pré-protocolo': 'var(--pie-4)',
    Tecnologia: 'var(--pie-7)',
    Jurídico: 'var(--pie-3)',
    Financeiro: 'var(--pie-5)',
    Estratégico: 'var(--pie-8)',
}

export function areaColor(area: string): string {
    return AREA_COLORS[area] ?? 'var(--pie-rest)'
}

function safeLocal(): Storage | null {
    try {
        return window.localStorage
    } catch {
        return null
    }
}
