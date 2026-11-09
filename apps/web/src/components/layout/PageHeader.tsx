import type { ReactNode } from 'react'

type PageHeaderProps = {
    title: string
    description?: string
    badge?: ReactNode // selo antes do título (ex.: "Plataforma")
    actions?: ReactNode // botões à direita (ex.: "Convidar pessoas")
}

// Módulo: o topo de toda página do menu (título, explicação e ações), como no protótipo.
export function PageHeader({ title, description, badge, actions }: PageHeaderProps) {
    return (
        <div className="page-header">
            <div className="stack" style={{ gap: 6 }}>
                {badge ? (
                    <div className="row" style={{ gap: 10 }}>
                        {badge}
                        <h1 className="h1">{title}</h1>
                    </div>
                ) : (
                    <h1 className="h1">{title}</h1>
                )}
                {description && <p className="muted">{description}</p>}
            </div>
            {actions && <div className="page-actions">{actions}</div>}
        </div>
    )
}
