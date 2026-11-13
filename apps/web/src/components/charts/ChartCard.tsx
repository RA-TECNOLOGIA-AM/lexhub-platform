import type { ReactNode } from 'react'

type ChartCardProps = {
    title: string
    subtitle?: ReactNode // linha menor embaixo do título
    tag?: ReactNode // selo ao lado do título (ex.: "Série Anual (Jan – Dez)")
    action?: ReactNode // à direita do cabeçalho (ex.: "Meta diária: 20")
    footer?: ReactNode // depois do divisor, embaixo do gráfico
    className?: string // posição na grade da seção
    children: ReactNode
}

// Módulo: a moldura de um gráfico: cabeçalho (título, subtítulo, selo e ação), o gráfico e um rodapé opcional.
export function ChartCard({ title, subtitle, tag, action, footer, className, children }: ChartCardProps) {
    return (
        <figure className={className ? `card chart ${className}` : 'card chart'}>
            <figcaption className="chart-head">
                <span className="chart-head-text">
                    <span className="chart-title">
                        {title}
                        {tag}
                    </span>
                    {subtitle && <span className="chart-sub">{subtitle}</span>}
                </span>
                {action}
            </figcaption>
            <div className="chart-body">{children}</div>
            {footer && <div className="chart-foot">{footer}</div>}
        </figure>
    )
}

// Gráfico sem dado no período (em vez de um eixo vazio).
export function ChartEmpty({ children = 'Sem dados no período.' }: { children?: ReactNode }) {
    return <p className="chart-empty muted small">{children}</p>
}
