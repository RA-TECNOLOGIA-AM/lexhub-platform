import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import type { KeyboardEvent, ReactNode } from 'react'

type SortableCardProps = {
    id: string // a key do dashboard
    section: string // em qual seção o card está
    children: ReactNode // o card de verdade (DashboardCard), que não sabe que é arrastável
}

// Módulo: embrulha um card para ele poder ser arrastado e reordenado.
export function SortableCard({ id, section, children }: SortableCardProps) {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
        id,
        data: { section },
        attributes: { roleDescription: 'card arrastável' },
    })

    // Teclado: só arrasta com o foco no próprio card. Espaço na estrela ou no link continua sendo deles.
    const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
        if (event.target === event.currentTarget) listeners?.onKeyDown?.(event)
    }

    return (
        <div
            ref={setNodeRef}
            className={isDragging ? 'sortable-card dragging' : 'sortable-card'}
            style={{ transform: CSS.Translate.toString(transform), transition }}
            {...attributes}
            {...listeners}
            onKeyDown={onKeyDown}
            onDragStart={(event) => event.preventDefault()} // impede o "arrastar link" do próprio navegador
        >
            {children}
        </div>
    )
}
