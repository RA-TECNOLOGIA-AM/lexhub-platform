import type { ReactNode } from 'react'

type PageHeaderProps = {
    title: string
    description?: string
    actions?: ReactNode // botões à direita (ex.: "Convidar pessoas")
}

// Módulo: o topo de toda página do menu (título, explicação e ações), como no protótipo.
export function PageHeader({ title, description, actions }: PageHeaderProps) {
    return (
        <div className="page-header">
            <div className="stack" style={{ gap: 6 }}>
                <h1 className="h1">{title}</h1>
                {description && <p className="muted">{description}</p>}
            </div>
            {actions && <div className="page-actions">{actions}</div>}
        </div>
    )
}
