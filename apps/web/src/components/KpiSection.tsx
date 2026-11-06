import type { ReactNode } from 'react'

type KpiSectionProps = {
    id: string // liga o título à seção (acessibilidade); único na página
    title: string
    subtitle?: string
    children: ReactNode // os <Kpi> da seção
}

// Módulo: um bloco de KPIs com título e explicação ("No período", "Situação atual do setor").
export function KpiSection({ id, title, subtitle, children }: KpiSectionProps) {
    return (
        <section className="stack" aria-labelledby={id}>
            <div>
                <h2 className="h2" id={id}>
                    {title}
                </h2>
                {subtitle && <p className="muted small">{subtitle}</p>}
            </div>
            <div className="grid grid-kpi">{children}</div>
        </section>
    )
}
