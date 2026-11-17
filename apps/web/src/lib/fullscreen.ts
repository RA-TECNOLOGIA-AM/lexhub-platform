// Módulo: tela cheia do navegador pelo botão da topbar (Fullscreen API), sem React (testado em fullscreen.test.ts).
// O F11 do navegador não passa por aqui (não dá para ler nem sair dele por código); o layout se ajusta sozinho.

export type FullscreenDoc = {
    fullscreenEnabled?: boolean
    fullscreenElement?: Element | null
    exitFullscreen?: () => Promise<void>
    documentElement: { requestFullscreen?: () => Promise<void> }
}

export type FullscreenResult = 'entered' | 'exited' | 'denied' | 'unsupported'

// Sem suporte (ex.: Safari do iPhone) ou bloqueado (iframe sem permissão): o botão nem aparece.
export function fullscreenSupported(doc: FullscreenDoc = document): boolean {
    return !!doc.fullscreenEnabled && typeof doc.documentElement.requestFullscreen === 'function'
}

export function isFullscreen(doc: FullscreenDoc = document): boolean {
    return !!doc.fullscreenElement
}

// Entra ou sai. A recusa do navegador (sem gesto da pessoa, política da página) vira 'denied', sem erro.
export async function toggleFullscreen(doc: FullscreenDoc = document): Promise<FullscreenResult> {
    if (!fullscreenSupported(doc)) return 'unsupported'
    try {
        if (isFullscreen(doc)) {
            await doc.exitFullscreen?.()
            return 'exited'
        }
        await doc.documentElement.requestFullscreen?.()
        return 'entered'
    } catch {
        return 'denied'
    }
}
