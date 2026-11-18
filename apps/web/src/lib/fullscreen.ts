// Módulo: tela cheia do navegador pelo botão da topbar (Fullscreen API), sem React (testado em fullscreen.test.ts).
// O F11 do navegador não passa por aqui (não dá para ler nem sair dele por código); o layout se ajusta sozinho.
// Só a tela cheia pedida pelo botão do app esconde a barra lateral: ela marca o <html> com data-app-fullscreen,
// e o CSS olha essa marca, não :fullscreen. No macOS o botão verde da janela (Safari, app instalado) pode ligar a
// mesma Fullscreen API, e aí :fullscreen também valeria e a barra sumia sem a pessoa ter pedido.

export type FullscreenDoc = {
    fullscreenEnabled?: boolean
    fullscreenElement?: Element | null
    exitFullscreen?: () => Promise<void>
    documentElement: { requestFullscreen?: () => Promise<void>; dataset?: DOMStringMap }
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
        setAppFlag(doc, true)
        await doc.documentElement.requestFullscreen?.()
        return 'entered'
    } catch {
        syncAppFullscreen(doc)
        return 'denied'
    }
}

// Chamar no 'fullscreenchange': saiu da tela cheia (Esc, botão, botão verde) = tira a marca do app.
export function syncAppFullscreen(doc: FullscreenDoc = document): void {
    if (!isFullscreen(doc)) setAppFlag(doc, false)
}

export function isAppFullscreen(doc: FullscreenDoc = document): boolean {
    return doc.documentElement.dataset?.appFullscreen === 'true'
}

function setAppFlag(doc: FullscreenDoc, on: boolean): void {
    const data = doc.documentElement.dataset
    if (!data) return
    if (on) data.appFullscreen = 'true'
    else delete data.appFullscreen
}
