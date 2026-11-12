import { useContext } from 'react'
import { TransitionContext } from './PageTransitionContext.ts'

export function usePageTransition() {
    const context = useContext(TransitionContext)

    if (!context) {
        throw new Error('usePageTransition deve ser usado dentro de PageTransitionProvider')
    }

    return context
}
