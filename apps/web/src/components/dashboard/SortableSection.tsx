import { useDndContext, useDroppable } from '@dnd-kit/core'
import { rectSortingStrategy, SortableContext } from '@dnd-kit/sortable'
import type { ReactNode } from 'react'
import { CardSection } from './CardSection.tsx'

type SortableSectionProps = {
    title: string
    ids: string[] // keys dos cards desta seção, na ordem da tela
    acceptsOthers?: boolean // aceita card de outra seção? (Favoritos: sim)
    children: ReactNode
}

// Módulo: uma seção do hub onde os cards se reordenam e, se acceptsOthers, onde dá para soltar card de fora.
export function SortableSection({ title, ids, acceptsOthers = false, children }: SortableSectionProps) {
    const { setNodeRef } = useDroppable({ id: `section:${title}`, data: { section: title, kind: 'section' } })
    const { active, over } = useDndContext()
    // Destaca só quando um card de OUTRA seção está por cima e esta seção aceita recebê-lo.
    const highlight =
        acceptsOthers && !!active && active.data.current?.section !== title && over?.data.current?.section === title

    return (
        <div ref={setNodeRef} className={highlight ? 'drop-zone over' : 'drop-zone'}>
            <SortableContext id={title} items={ids} strategy={rectSortingStrategy}>
                <CardSection title={title}>{children}</CardSection>
            </SortableContext>
        </div>
    )
}
