import { createContext } from 'react'
import type { To } from 'react-router'

export interface TransitionContextType {
    transitionTo: (to: To) => void
}

export const TransitionContext = createContext<TransitionContextType | undefined>(undefined)
