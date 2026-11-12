import { useContext, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { TopbarSlotContext } from './topbar-slot.ts'

// Módulo: um espaço na topbar que uma página pode ocupar (ex.: o Período de um dashboard).
// O AppLayout guarda o elemento do espaço (TopbarSlotContext); a página desenha lá dentro com <TopbarPortal>.
// Quando a página sai da tela, o conteúdo some da topbar junto.
export function TopbarPortal({ children }: { children: ReactNode }) {
    const slot = useContext(TopbarSlotContext)
    return slot ? createPortal(children, slot) : null
}
