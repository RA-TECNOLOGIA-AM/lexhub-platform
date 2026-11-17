import { Icon } from '../ui/Icon.tsx'
import { useFullscreen } from '../../hooks/useFullscreen.ts'

// Módulo: botão da topbar que entra e sai da tela cheia (como o F11, mas pelo site).
// Navegador sem suporte: o botão não aparece. Recusa: o botão continua e avisa no texto.
export function FullscreenToggle() {
    const { supported, active, denied, toggle } = useFullscreen()
    if (!supported) return null

    const label = active ? 'Sair da tela cheia' : 'Tela cheia'
    const title = denied ? 'O navegador não liberou a tela cheia (tente o F11)' : label

    return (
        <button className="iconbtn" type="button" aria-label={label} title={title} onClick={() => void toggle()}>
            <Icon name={active ? 'minimize' : 'maximize'} />
        </button>
    )
}
