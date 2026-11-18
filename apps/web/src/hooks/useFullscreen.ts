import { useEffect, useState } from 'react'
import {
    fullscreenSupported,
    isFullscreen,
    syncAppFullscreen,
    toggleFullscreen,
    type FullscreenResult,
} from '../lib/fullscreen.ts'

// Hook: estado da tela cheia (acompanha o Esc do navegador) e a troca pelo botão.
export function useFullscreen(): {
    supported: boolean
    active: boolean
    denied: boolean
    toggle: () => Promise<FullscreenResult>
} {
    const [active, setActive] = useState(() => isFullscreen())
    const [denied, setDenied] = useState(false)
    const supported = fullscreenSupported()

    useEffect(() => {
        const onChange = () => {
            syncAppFullscreen()
            setActive(isFullscreen())
        }
        document.addEventListener('fullscreenchange', onChange)
        return () => document.removeEventListener('fullscreenchange', onChange)
    }, [])

    const toggle = async () => {
        const result = await toggleFullscreen()
        setDenied(result === 'denied')
        return result
    }

    return { supported, active, denied, toggle }
}
