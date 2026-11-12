import { createContext } from 'react'

// O elemento do espaço da topbar que uma página pode ocupar (null = ainda não montado). Ver TopbarSlot.tsx.
export const TopbarSlotContext = createContext<HTMLElement | null>(null)
