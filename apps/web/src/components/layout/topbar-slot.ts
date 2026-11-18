import { createContext } from 'react'

// Os espaços da topbar que uma página pode ocupar (null = ainda não montado). Ver TopbarSlot.tsx.
// start = à esquerda (ex.: nome do dashboard); end = à direita, antes do sino (ex.: Filtros e Período).
export type TopbarSlots = { start: HTMLElement | null; end: HTMLElement | null }

export const TopbarSlotContext = createContext<TopbarSlots>({ start: null, end: null })
