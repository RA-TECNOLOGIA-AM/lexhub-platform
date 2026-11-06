import type { ReactNode } from 'react'
import { Icon, type IconName } from '../Icon.tsx'

type StateMessageProps = {
    icon: IconName
    title: string
    children?: ReactNode // texto de explicação
    action?: ReactNode // botão ou link (opcional)
    alert?: boolean // true = leitor de tela anuncia na hora (erros)
}

// Módulo: o cartão centralizado de "estado" (ícone + título + texto + ação) do template.
// Base de ErrorState e dos estados vazios: cada um só passa o conteúdo.
export function StateMessage({ icon, title, children, action, alert = false }: StateMessageProps) {
    return (
        <div className="card empty" role={alert ? 'alert' : undefined}>
            <span className="icon">
                <Icon name={icon} size={22} />
            </span>
            <h2 className="h2">{title}</h2>
            {children && <p className="muted small">{children}</p>}
            {action}
        </div>
    )
}