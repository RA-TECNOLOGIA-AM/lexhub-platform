import type { CSSProperties, ReactNode } from 'react'

type CardSectionProps = {
    title: string
    color?: string // cor da área (areaColor): bolinha no título e borda nos cards, como no Quadro; sem = neutro
    children: ReactNode // os cards
}

// Módulo: um bloco do hub com título e a grade de cards.
export function CardSection({ title, color, children }: CardSectionProps) {
    return (
        <section
            className={color ? 'stack card-section has-color' : 'stack card-section'}
            style={color ? ({ '--col': color } as CSSProperties) : undefined}
            aria-label={title}
        >
            <h2 className="h2 card-section-title">
                {color && <span className="board-dot" aria-hidden="true" />}
                {title}
            </h2>
            <div className="grid grid-cards">{children}</div>
        </section>
    )
}
