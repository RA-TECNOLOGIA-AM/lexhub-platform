import { Icon } from '../ui/Icon.tsx'
import { LogoJustica } from '../ui/LogoJustica.tsx'

type SidebarToggleProps = {
    collapsed: boolean
    onToggle: () => void
}

// Módulo: o logo do LexHub no topo da barra lateral, que também recolhe e expande a barra.
// Ao passar o mouse (ou focar pelo teclado) o logo vira o ícone de painel, para mostrar que é clicável.
export function SidebarToggle({ collapsed, onToggle }: SidebarToggleProps) {
    const label = collapsed ? 'Expandir menu lateral' : 'Recolher menu lateral'

    return (
        <button
            className="brand-toggle"
            type="button"
            aria-label={label}
            aria-expanded={!collapsed}
            title={label}
            onClick={onToggle}
        >
            <LogoJustica size={28} className="brand-toggle-logo" />
            <span className="brand-toggle-icon">
                <Icon name="panel-left" />
            </span>
        </button>
    )
}
