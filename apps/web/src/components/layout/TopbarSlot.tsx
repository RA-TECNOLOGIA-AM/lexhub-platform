import { useContext, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { TopbarSlotContext } from './topbar-slot.ts'

type TopbarPortalProps = {
    children: ReactNode
    place?: 'start' | 'end' // start = à esquerda (nome da página); end = à direita, antes do sino (padrão)
}

// Módulo: um espaço na topbar que uma página pode ocupar (ex.: o nome e o Período de um dashboard).
// O AppLayout guarda os elementos dos espaços (TopbarSlotContext); a página desenha lá dentro com <TopbarPortal>.
// Quando a página sai da tela, o conteúdo some da topbar junto.
export function TopbarPortal({ children, place = 'end' }: TopbarPortalProps) {
    const slot = useContext(TopbarSlotContext)[place]
    return slot ? createPortal(children, slot) : null
}
