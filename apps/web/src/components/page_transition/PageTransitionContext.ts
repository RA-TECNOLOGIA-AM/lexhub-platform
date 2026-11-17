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

// Coluna do conteúdo do AppLayout (topbar + miolo): com ela na tela, a logo cobre só o miolo
// (menu lateral e topbar ficam à vista). Sem ela (login, abertura do app), cobre a tela inteira.
export type RegisterTransitionArea = (element: HTMLElement | null) => void

export const TransitionAreaContext = createContext<RegisterTransitionArea | undefined>(undefined)
