import { createContext } from 'react'
import type { To } from 'react-router'

export interface TransitionContextType {
    transitionTo: (to: To) => void
}

export const TransitionContext = createContext<TransitionContextType | undefined>(undefined)

// "Ainda estou carregando": quem chama segura o overlay da transição até devolver (a função retornada).
// Fica num contexto separado e estável para não re-renderizar quem só usa o transitionTo.
export type HoldTransition = () => () => void

export const TransitionHoldContext = createContext<HoldTransition | undefined>(undefined)
