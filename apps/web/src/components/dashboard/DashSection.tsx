import { useId, useState, type ReactNode } from 'react'
import { Icon } from '../ui/Icon.tsx'

type DashSectionProps = {
    index: number // 1 -> "01"
    eyebrow: string // "Visão geral"
    title: string // "Indicadores do período"
    subtitle?: string
    action?: ReactNode // controle da seção ao lado do "Ocultar" (ex.: Total | Entrada); some com a seção oculta
    children: ReactNode
}

// Módulo: uma seção numerada de dashboard, como na v1 (01 · Visão geral · título · Ocultar).
// Ocultar só esconde nesta visita: recarregar a página mostra tudo de novo.
export function DashSection({ index, eyebrow, title, subtitle, action, children }: DashSectionProps) {
    const [open, setOpen] = useState(true)
    const id = useId()
    return (
        <section className="dsec" aria-labelledby={`${id}-t`}>
            <header className="dsec-head">
                <span className="dsec-num" aria-hidden="true">
                    {String(index).padStart(2, '0')}
                </span>
                <div className="dsec-text">
                    <span className="dsec-eyebrow">{eyebrow}</span>
                    <h2 className="dsec-title" id={`${id}-t`}>
                        {title}
                    </h2>
                    {subtitle && <p className="dsec-sub">{subtitle}</p>}
                </div>
                {action && open && <div className="dsec-action">{action}</div>}
                <button
                    type="button"
                    className="btn dsec-toggle"
                    aria-expanded={open}
                    aria-controls={`${id}-b`}
                    onClick={() => setOpen((o) => !o)}
                >
                    <Icon name={open ? 'chevron-up' : 'chevron-down'} size={16} />
                    {open ? 'Ocultar' : 'Mostrar'}
                </button>
            </header>
            <div id={`${id}-b`} hidden={!open}>
                {children}
            </div>
        </section>
    )
}
