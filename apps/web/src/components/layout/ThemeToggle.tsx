import { Icon } from '../ui/Icon.tsx'
import { useTheme } from '../../hooks/useTheme.ts'

// Módulo: botão da topbar (ao lado do sino) que alterna entre modo claro e escuro (a escolha fica lembrada).
// Mostra o ícone do tema para onde vai: lua no claro, sol no escuro.
export function ThemeToggle() {
    const { theme, toggle } = useTheme()
    const label = theme === 'dark' ? 'Usar modo claro' : 'Usar modo escuro'

    return (
        <button className="iconbtn" type="button" aria-label={label} title={label} onClick={toggle}>
            <Icon name={theme === 'dark' ? 'sun' : 'moon'} />
        </button>
    )
}
