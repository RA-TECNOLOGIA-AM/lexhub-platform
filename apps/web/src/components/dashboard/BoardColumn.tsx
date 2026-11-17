import { useDndContext, useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import type { CSSProperties, ReactNode } from 'react'
import { areaColor } from '../../lib/hubView.ts'

type BoardColumnProps = {
    title: string // a área (ou Favoritos); é também o nome da seção no arraste
    ids: string[] // keys dos cards desta coluna, na ordem da tela
    acceptsOthers?: boolean // aceita card de outra coluna? (Favoritos: sim)
    empty?: ReactNode // o que mostrar sem cards; sem isso, a coluna vazia vira uma faixa estreita
    children: ReactNode // os cards
}

// Módulo: uma coluna do hub em "Quadro" (cabeçalho com cor e contagem, cards um embaixo do outro).
// Mesmo contrato de arraste da SortableSection: reordena dentro e, se acceptsOthers, recebe card de fora.
export function BoardColumn({ title, ids, acceptsOthers = false, empty, children }: BoardColumnProps) {
    const { setNodeRef } = useDroppable({ id: `section:${title}`, data: { section: title, kind: 'section' } })
    const { active, over } = useDndContext()
    const highlight =
        acceptsOthers && !!active && active.data.current?.section !== title && over?.data.current?.section === title
    const collapsed = ids.length === 0 && !empty
    const className = ['board-col', collapsed && 'collapsed', highlight && 'over'].filter(Boolean).join(' ')

    return (
        <section
            ref={setNodeRef}
            className={className}
            style={{ '--col': areaColor(title) } as CSSProperties}
            aria-label={`${title}: ${ids.length}`}
        >
            <header className="board-col-head">
                <span className="board-dot" aria-hidden="true" />
                <h2 className="board-col-title">{title}</h2>
                <span className="board-count">{ids.length}</span>
            </header>
            {!collapsed && (
                <SortableContext id={title} items={ids} strategy={verticalListSortingStrategy}>
                    <div className="board-cards">{ids.length > 0 ? children : empty}</div>
                </SortableContext>
            )}
        </section>
    )
}
