import {
    closestCenter,
    DndContext,
    KeyboardSensor,
    MouseSensor,
    pointerWithin,
    TouchSensor,
    useSensor,
    useSensors,
    type Active,
    type Announcements,
    type CollisionDetection,
    type DragEndEvent,
    type Over,
} from '@dnd-kit/core'
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import type { ReactNode } from 'react'
import { suppressNextClick } from '../../lib/suppressNextClick.ts'

// O que aconteceu ao soltar: qual card (active), de qual seção (from),
// sobre qual card (over; null = num espaço vazio da seção) e em qual seção (to).
export type HubDrop = { active: string; from: string; over: string | null; to: string }

// Cards e seções levam { section } nos dados; a seção leva também kind: 'section'.
type DropData = { section: string; kind?: 'section' }
const dataOf = (item: Active | Over) => item.data.current as DropData | undefined

// Mouse ou dedo: vale o que está embaixo do ponteiro, preferindo o card à seção em volta dele.
// Teclado não tem ponteiro: vale o mais perto (closestCenter).
const collision: CollisionDetection = (args) => {
    const hits = pointerWithin(args)
    if (hits.length === 0) return closestCenter(args)
    const cards = hits.filter((hit) => hit.data?.droppableContainer?.data.current?.kind !== 'section')
    return cards.length > 0 ? cards : hits
}

// O que o leitor de tela fala (o padrão da biblioteca é em inglês).
const INSTRUCTIONS = 'Para mover um card: aperte espaço, use as setas e aperte espaço de novo para soltar. Esc cancela.'
const ANNOUNCEMENTS: Announcements = {
    onDragStart: ({ active }) => `Pegou o card ${active.id}.`,
    onDragOver: ({ over }) => (over ? `Sobre ${over.id}.` : 'Fora das seções.'),
    onDragEnd: ({ over }) => (over ? `Soltou sobre ${over.id}.` : 'Soltou fora das seções.'),
    onDragCancel: () => 'Movimento cancelado.',
}

type HubDndProps = {
    onDrop: (drop: HubDrop) => void // quem usa decide o que fazer (reordenar, favoritar...)
    children: ReactNode
}

// Módulo: liga o arrastar no hub (mouse, toque e teclado) e avisa o que foi solto e onde.
// Esconde: a dnd-kit inteira. A página não importa nada dela.
export function HubDnd({ onDrop, children }: HubDndProps) {
    const sensors = useSensors(
        useSensor(MouseSensor, { activationConstraint: { distance: 8 } }), // só arrasta depois de 8 px: o clique continua abrindo
        useSensor(TouchSensor, { activationConstraint: { delay: 250, tolerance: 5 } }), // no celular, segurar; deslizar rola a página
        useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
    )

    function handleDragEnd({ active, over }: DragEndEvent) {
        suppressNextClick()
        const from = dataOf(active)?.section
        const target = over ? dataOf(over) : undefined
        if (!from || !over || !target) return // soltou fora de qualquer seção
        onDrop({
            active: String(active.id),
            from,
            over: target.kind === 'section' ? null : String(over.id),
            to: target.section,
        })
    }

    return (
        <DndContext
            sensors={sensors}
            collisionDetection={collision}
            onDragEnd={handleDragEnd}
            accessibility={{ screenReaderInstructions: { draggable: INSTRUCTIONS }, announcements: ANNOUNCEMENTS }}
        >
            {children}
        </DndContext>
    )
}
