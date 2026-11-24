import { Icon } from '../ui/Icon.tsx'
import { useAppearance } from '../../contexts/appearance-context.ts'

// Módulo: botão da topbar que alterna entre modo claro e escuro (atalho de Configurações → Aparência).
// Troca só o modo: cada modo mantém o tema escolhido na galeria. A escolha fica salva na conta.
// Mostra o ícone do modo para onde vai: lua no claro, sol no escuro.
export function ThemeToggle() {
    const { resolved, setMode } = useAppearance()
    const dark = resolved.mode === 'dark'
    const label = dark ? 'Usar modo claro' : 'Usar modo escuro'

    return (
        <button
            className="iconbtn"
            type="button"
            aria-label={label}
            title={label}
            onClick={() => setMode(dark ? 'light' : 'dark')}
        >
            <Icon name={dark ? 'sun' : 'moon'} />
        </button>
    )
}
