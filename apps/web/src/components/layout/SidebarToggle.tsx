import { Icon } from '../ui/Icon.tsx'

type SidebarToggleProps = {
    collapsed: boolean
    onToggle: () => void
}

// Módulo: botão da topbar (só no computador) que recolhe a barra lateral para os ícones e abre de novo.
// No celular quem aparece é o botão de menu (a barra lateral vira gaveta).
export function SidebarToggle({ collapsed, onToggle }: SidebarToggleProps) {
    const label = collapsed ? 'Expandir menu lateral' : 'Recolher menu lateral'

    return (
        <button
            className="iconbtn side-toggle"
            type="button"
            aria-label={label}
            aria-expanded={!collapsed}
            title={label}
            onClick={onToggle}
        >
            <Icon name="panel-left" />
        </button>
    )
}
