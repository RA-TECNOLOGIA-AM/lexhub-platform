import type { ReactNode } from 'react'

type CardSectionProps = {
    title: string
    children: ReactNode // os cards
}

// Módulo: um bloco do hub com título e a grade de cards.
export function CardSection({ title, children }: CardSectionProps) {
    return (
        <section className="stack" aria-label={title}>
            <h2 className="h2">{title}</h2>
            <div className="grid grid-cards">{children}</div>
        </section>
    )
}
